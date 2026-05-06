# apps/reports/services.py
from django.db.models import Count, Sum, Q, Avg, F, DurationField, ExpressionWrapper
from django.db.models.functions import ExtractHour, ExtractWeekDay, ExtractSecond, ExtractMinute, TruncDate
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.bookings.models import Booking
from apps.spaces.models import Space


class ReportService:
    """Сервис для агрегации данных отчётов"""
    
    def __init__(self, user, period_days=30):
        self.user = user
        self.period_days = period_days
        self.start_date = self._get_start_date()
    
    def _get_start_date(self):
        """Получить дату начала периода"""
        if self.period_days == 0:
            return timezone.datetime(2020, 1, 1, tzinfo=timezone.get_current_timezone())
        return timezone.now() - timedelta(days=self.period_days)
    
    def get_bookings_queryset(self):
        """Получить базовый QuerySet бронирований пользователя за период"""
        return Booking.objects.filter(
            user=self.user,
            created_at__gte=self.start_date
        ).select_related('space')
    
    def get_basic_stats(self):
        """Базовая статистика бронирований (один запрос к БД)"""
        bookings = self.get_bookings_queryset()
        
        # Используем агрегацию Django ORM вместо нескольких запросов
        stats = bookings.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status__in=['pending', 'confirmed'], check_out__gte=timezone.now())),
            completed=Count('id', filter=Q(status='confirmed', check_out__lt=timezone.now())),
            cancelled=Count('id', filter=Q(status='cancelled'))
        )
        
        total = stats['total']
        
        return {
            'total_bookings': total,
            'active_bookings': stats['active'],
            'completed_bookings': stats['completed'],
            'cancelled_bookings': stats['cancelled'],
            'cancellation_rate': round((stats['cancelled'] / total * 100), 1) if total > 0 else 0,
        }
    
    def get_time_stats(self):
        """Статистика по времени бронирований (агрегация в БД)"""
        bookings = self.get_bookings_queryset()
        
        # Вычисляем длительность на уровне БД
        duration_expr = ExpressionWrapper(
            F('check_out') - F('check_in'),
            output_field=DurationField()
        )
        
        # Получаем среднюю и суммарную длительность через ORM
        time_stats = bookings.filter(
            check_in__isnull=False, 
            check_out__isnull=False
        ).aggregate(
            total_seconds=Sum(ExtractHour(duration_expr) * 3600 + 
                           ExtractMinute(duration_expr) * 60 + 
                           ExtractSecond(duration_expr)),
            avg_seconds=Avg(ExtractHour(duration_expr) * 3600 + 
                           ExtractMinute(duration_expr) * 60 + 
                           ExtractSecond(duration_expr))
        )
        
        total_seconds = time_stats['total_seconds'] or 0
        avg_seconds = time_stats['avg_seconds'] or 0
        
        total_hours = total_seconds / 3600
        avg_hours = avg_seconds / 3600
        
        # Частота бронирований в месяц
        total_bookings = bookings.count()
        days_in_period = self.period_days if self.period_days > 0 else 365
        frequency = (total_bookings / (days_in_period / 30)) if days_in_period > 0 else 0
        
        return {
            'total_hours': round(total_hours, 1),
            'avg_duration': round(avg_hours, 1),
            'frequency': round(frequency, 1),
        }
    
    def get_daily_stats(self):
        """Статистика по дням (GROUP BY в БД)"""
        bookings = self.get_bookings_queryset()
        
        # Группировка на уровне БД с помощью TruncDate
        daily_data = (
            bookings
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        dates = []
        counts = []
        for item in daily_data:
            date_str = item['date'].strftime('%d.%m') if item['date'] else '—'
            dates.append(date_str)
            counts.append(item['count'])
        
        return {
            'dates': dates,
            'bookings_by_date': counts,
        }
    
    def get_spaces_popularity(self):
        """Популярность помещений (GROUP BY в БД)"""
        bookings = self.get_bookings_queryset()
        
        # Группировка на уровне БД
        space_data = (
            bookings
            .values('space__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        return {
            'space_names': [item['space__name'] for item in space_data],
            'space_bookings': [item['count'] for item in space_data],
        }
    
    def get_weekday_stats(self):
        """Активность по дням недели (GROUP BY в БД)"""
        bookings = self.get_bookings_queryset()
        weekday_names = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
        
        # Извлечение дня недели на уровне БД
        weekday_data = (
            bookings
            .annotate(weekday=ExtractWeekDay('created_at'))
            .values('weekday')
            .annotate(count=Count('id'))
            .order_by('weekday')
        )
        
        # Заполняем массив результатов (0=воскресенье в Django, преобразуем к 0=понедельник)
        weekday_counts = [0] * 7
        for item in weekday_data:
            # Django ExtractWeekDay: 1=воскресенье, 2=понедельник... 7=суббота
            dj_weekday = int(item['weekday'])
            # Преобразуем к 0=понедельник
            idx = (dj_weekday + 5) % 7
            weekday_counts[idx] = item['count']
        
        return {
            'weekday_labels': weekday_names,
            'weekday_stats': weekday_counts,
        }
    
    def get_hourly_stats(self):
        """Популярные часы бронирования (GROUP BY в БД)"""
        bookings = self.get_bookings_queryset()
        
        # Извлечение часа на уровне БД
        hour_data = (
            bookings
            .filter(check_in__isnull=False)
            .annotate(hour=ExtractHour('check_in'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
        )
        
        hour_counts = [0] * 24
        for item in hour_data:
            hour = int(item['hour'])
            hour_counts[hour] = item['count']
        
        # Возвращаем только часы с бронированиями
        popular_hours = []
        popular_counts = []
        for hour in range(24):
            if hour_counts[hour] > 0:
                popular_hours.append(hour)
                popular_counts.append(hour_counts[hour])
        
        return {
            'popular_hours': popular_hours,
            'popular_hours_counts': popular_counts,
        }
    
    def get_status_breakdown(self):
        """Разбивка по статусам (GROUP BY в БД)"""
        bookings = self.get_bookings_queryset()
        
        status_map = {
            'pending': 'Ожидает',
            'confirmed': 'Подтверждено',
            'cancelled': 'Отменено',
        }
        
        # Группировка на уровне БД
        status_data = (
            bookings
            .values('status')
            .annotate(count=Count('id'))
        )
        
        status_counts = {'pending': 0, 'confirmed': 0, 'cancelled': 0}
        for item in status_data:
            status_counts[item['status']] = item['count']
        
        return {
            'status_breakdown': status_counts,
            'status_labels': list(status_map.values()),
        }
    
    def get_recent_bookings(self, limit=10):
        """Последние бронирования"""
        bookings = self.get_bookings_queryset().order_by('-created_at')[:limit]
        
        recent = []
        for booking in bookings:
            duration = 0
            if booking.check_in and booking.check_out:
                duration = (booking.check_out - booking.check_in).total_seconds() / 3600
            
            recent.append({
                'space_name': booking.space.name,
                'date': booking.created_at.strftime('%d.%m.%Y'),
                'time': f"{booking.check_in.strftime('%H:%M')} - {booking.check_out.strftime('%H:%M')}" if booking.check_in else '-',
                'duration': f"{duration:.1f} ч" if duration > 0 else '-',
                'status': booking.status,
                'status_display': dict(Booking.STATUS_CHOICES).get(booking.status, booking.status),
            })
        
        return {'recent_bookings': recent}
    
    def get_insights(self):
        """Генерация персонализированных инсайтов"""
        basic = self.get_basic_stats()
        time_stats = self.get_time_stats()
        weekday_stats = self.get_weekday_stats()
        
        insights = []
        
        if basic['total_bookings'] == 0:
            insights.append({
                'type': 'info',
                'message': '📭 У вас пока нет бронирований. Перейдите в раздел "Помещения", чтобы забронировать пространство!'
            })
            return insights
        
        # Анализ дня недели
        if weekday_stats['weekday_stats']:
            max_count = max(weekday_stats['weekday_stats'])
            if max_count > 0:
                max_index = weekday_stats['weekday_stats'].index(max_count)
                days = ['понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу', 'воскресенье']
                insights.append({
                    'type': 'trend',
                    'message': f'⭐ Вы чаще всего бронируете помещения в {days[max_index]}. Это ваш самый активный день!'
                })
        
        # Анализ отмен
        if basic['cancellation_rate'] > 30:
            insights.append({
                'type': 'warning',
                'message': f'⚠️ Ваш процент отмен ({basic["cancellation_rate"]}%) выше среднего. Попробуйте планировать бронирования заранее.'
            })
        elif basic['cancellation_rate'] > 0:
            insights.append({
                'type': 'info',
                'message': f'📊 Ваш процент отмен составляет {basic["cancellation_rate"]}%.'
            })
        
        # Анализ длительности
        if time_stats['avg_duration'] > 3:
            insights.append({
                'type': 'success',
                'message': f'💡 Вы бронируете помещения в среднем на {time_stats["avg_duration"]:.1f} часов. Это отличное время для продуктивной работы!'
            })
        
        # Анализ активности
        if time_stats['total_hours'] > 10:
            insights.append({
                'type': 'success',
                'message': f'🎉 Отлично! За выбранный период вы использовали помещения {time_stats["total_hours"]:.0f} часов. Так держать!'
            })
        
        if basic['total_bookings'] > 0:
            insights.append({
                'type': 'info',
                'message': f'📈 Уже {basic["total_bookings"]} бронирований — хороший результат. Продолжайте в том же духе!'
            })
        
        return insights
    
    def get_full_report(self):
        """Полный отчёт со всеми данными"""
        basic = self.get_basic_stats()
        time_stats = self.get_time_stats()
        daily = self.get_daily_stats()
        spaces = self.get_spaces_popularity()
        weekday = self.get_weekday_stats()
        hourly = self.get_hourly_stats()
        status = self.get_status_breakdown()
        recent = self.get_recent_bookings()
        insights = self.get_insights()
        
        return {
            **basic,
            **time_stats,
            **daily,
            **spaces,
            **weekday,
            **hourly,
            **status,
            **recent,
            'insights': insights,
        }
