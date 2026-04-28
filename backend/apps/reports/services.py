# apps/reports/services.py
from django.db.models import Count, Sum, Q, Avg, F, DurationField, ExpressionWrapper
from django.db.models.functions import ExtractHour, ExtractWeekDay, TruncDate, TruncMonth
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
        )
    
    def get_basic_stats(self):
        """Базовая статистика бронирований"""
        bookings = self.get_bookings_queryset()
        
        total = bookings.count()
        active = bookings.filter(
            status__in=['pending', 'confirmed'],
            end_time__gte=timezone.now()
        ).count()
        completed = bookings.filter(status='confirmed', end_time__lt=timezone.now()).count()
        cancelled = bookings.filter(status='cancelled').count()
        
        return {
            'total_bookings': total,
            'active_bookings': active,
            'completed_bookings': completed,
            'cancelled_bookings': cancelled,
            'cancellation_rate': round((cancelled / total * 100), 1) if total > 0 else 0,
        }
    
    def get_time_stats(self):
        """Статистика по времени бронирований"""
        bookings = self.get_bookings_queryset()
        
        # Общее время в часах
        total_hours = 0
        for booking in bookings:
            if booking.start_time and booking.end_time:
                duration = (booking.end_time - booking.start_time).total_seconds() / 3600
                total_hours += duration
        
        # Средняя длительность
        total_bookings = bookings.count()
        avg_duration = total_hours / total_bookings if total_bookings > 0 else 0
        
        # Частота бронирований в месяц
        days_in_period = self.period_days if self.period_days > 0 else 365
        frequency = (total_bookings / (days_in_period / 30)) if days_in_period > 0 else 0
        
        return {
            'total_hours': round(total_hours, 1),
            'avg_duration': round(avg_duration, 1),
            'frequency': round(frequency, 1),
        }
    
    def get_daily_stats(self):
        """Статистика по дням (для графика динамики)"""
        bookings = self.get_bookings_queryset()
        
        # Группировка по датам
        daily_counts = {}
        for booking in bookings.order_by('created_at'):
            date = booking.created_at.strftime('%d.%m')
            daily_counts[date] = daily_counts.get(date, 0) + 1
        
        return {
            'dates': list(daily_counts.keys()),
            'bookings_by_date': list(daily_counts.values()),
        }
    
    def get_spaces_popularity(self):
        """Популярность помещений"""
        bookings = self.get_bookings_queryset()
        
        space_counts = {}
        for booking in bookings:
            space_name = booking.space.name
            space_counts[space_name] = space_counts.get(space_name, 0) + 1
        
        # Сортируем и берем топ-5
        top_spaces = sorted(space_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'space_names': [item[0] for item in top_spaces],
            'space_bookings': [item[1] for item in top_spaces],
        }
    
    def get_weekday_stats(self):
        """Активность по дням недели (0=понедельник)"""
        bookings = self.get_bookings_queryset()
        
        weekday_counts = {i: 0 for i in range(7)}
        weekday_names = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
        
        for booking in bookings:
            if booking.created_at:
                weekday = booking.created_at.weekday()
                weekday_counts[weekday] = weekday_counts.get(weekday, 0) + 1
        
        return {
            'weekday_labels': weekday_names,
            'weekday_stats': [weekday_counts[i] for i in range(7)],
        }
    
    def get_hourly_stats(self):
        """Популярные часы бронирования"""
        bookings = self.get_bookings_queryset()
        
        hour_counts = {}
        for booking in bookings:
            if booking.start_time:
                hour = booking.start_time.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        sorted_hours = sorted(hour_counts.items())
        
        return {
            'popular_hours': [h for h, _ in sorted_hours],
            'popular_hours_counts': [c for _, c in sorted_hours],
        }
    
    def get_status_breakdown(self):
        """Разбивка по статусам"""
        bookings = self.get_bookings_queryset()
        
        status_map = {
            'pending': 'Ожидает',
            'confirmed': 'Подтверждено',
            'cancelled': 'Отменено',
        }
        
        status_counts = {
            'pending': bookings.filter(status='pending').count(),
            'confirmed': bookings.filter(status='confirmed').count(),
            'cancelled': bookings.filter(status='cancelled').count(),
        }
        
        return {
            'status_breakdown': status_counts,
            'status_labels': list(status_map.values()),
        }
    
    def get_recent_bookings(self, limit=10):
        """Последние бронирования"""
        bookings = self.get_bookings_queryset().order_by('-created_at')[:limit]
        
        recent = []
        for booking in bookings:
            duration = (booking.end_time - booking.start_time).total_seconds() / 3600 if booking.start_time and booking.end_time else 0
            
            recent.append({
                'space_name': booking.space.name,
                'date': booking.created_at.strftime('%d.%m.%Y'),
                'time': f"{booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}" if booking.start_time else '-',
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