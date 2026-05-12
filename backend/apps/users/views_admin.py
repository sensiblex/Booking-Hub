from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate, TruncWeek
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from apps.notifications.services import notify_space_moderation_changed

try:
    from apps.spaces.models import Space, SpacePhoto
    from apps.spaces.forms import SpaceForm
except ImportError:
    Space = None
    SpacePhoto = None
    SpaceForm = None

try:
    from apps.bookings.models import Booking
except ImportError:
    Booking = None

try:
    from apps.payments.models import Payment
except ImportError:
    Payment = None


@staff_member_required(login_url='/users/login/')
def admin_dashboard(request):
    User = get_user_model()
    context = {
        'users_count':    User.objects.count(),
        'spaces_count':   Space.objects.count()      if Space      else 0,
        'bookings_count': Booking.objects.count()    if Booking    else 0,
        'payments_count': Payment.objects.count()    if Payment    else 0,
    }
    return render(request, 'admin/dashboard.html', context)


@staff_member_required(login_url='/users/login/')
def admin_dashboard_api(request):
    User = get_user_model()

    allowed_periods = {7, 30, 365}
    period_days = request.GET.get('period', '30')
    try:
        period_days = int(period_days)
    except (TypeError, ValueError):
        period_days = 30
    if period_days not in allowed_periods:
        period_days = 30

    start_date = timezone.now() - timedelta(days=period_days)

    users_by_role = [
        {'role': row['role'], 'count': row['count']}
        for row in User.objects.values('role').annotate(count=Count('id')).order_by('role')
    ]

    bookings_qs = Booking.objects.filter(created_at__gte=start_date) if Booking else []
    payments_qs = Payment.objects.filter(created_at__gte=start_date) if Payment else []

    bookings_by_day = []
    bookings_by_week = []
    top_spaces = []
    if Booking:
        bookings_by_day = [
            {
                'date': row['day'].isoformat(),
                'count': row['count'],
            }
            for row in bookings_qs.annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        ]

        bookings_by_week = [
            {
                'week': row['week'].date().isoformat() if hasattr(row['week'], 'date') else row['week'].isoformat(),
                'count': row['count'],
            }
            for row in bookings_qs.annotate(week=TruncWeek('created_at'))
            .values('week')
            .annotate(count=Count('id'))
            .order_by('week')
        ]

        top_spaces = [
            {
                'space_id': row['space_id'],
                'space_name': row['space__name'],
                'bookings_count': row['bookings_count'],
            }
            for row in bookings_qs.values('space_id', 'space__name')
            .annotate(bookings_count=Count('id'))
            .order_by('-bookings_count', 'space__name')[:5]
        ]

    revenue_total = 0
    if Payment:
        revenue_total = payments_qs.aggregate(total=Sum('amount')).get('total') or 0

    payload = {
        'users_by_role': users_by_role,
        'bookings_by_day': bookings_by_day,
        'bookings_by_week': bookings_by_week,
        'revenue': {
            'period_total': revenue_total,
            'currency': 'RUB',
        },
        'top_spaces': top_spaces,
        'meta': {
            'period_days': period_days,
            'generated_at': timezone.now().isoformat(),
        },
    }
    return JsonResponse(payload)


# ---- Spaces ----

@staff_member_required(login_url='/users/login/')
def admin_spaces(request):
    pending_spaces = []
    if Space is None:
        spaces = []
    else:
        q = request.GET.get('q', '').strip()
        moderation_status = request.GET.get('moderation_status', '').strip()
        spaces = (
            Space.objects.select_related('submitted_by', 'category')
            .prefetch_related('amenities')
            .all()
            .order_by('-created_at')
        )
        if q:
            spaces = spaces.filter(
                Q(name__icontains=q) | Q(address__icontains=q)
            )
        if moderation_status:
            spaces = spaces.filter(moderation_status=moderation_status)
        pending_spaces = spaces.filter(moderation_status=Space.MODERATION_PENDING)
    return render(request, 'admin/spaces.html', {
        'spaces': spaces,
        'pending_spaces': pending_spaces,
    })


@staff_member_required(login_url='/users/login/')
def admin_space_create(request):
    if SpaceForm is None:
        messages.error(request, 'Модуль помещений недоступен.')
        return redirect('admin_spaces')

    form = SpaceForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            space = form.save()
            _create_space_photos(space, request.FILES.getlist('photos'))
            messages.success(request, 'Помещение успешно добавлено.')
            return redirect('admin_spaces')
        messages.error(request, 'Проверьте данные формы.')
    return render(request, 'admin/space_form.html', {
        'action': 'Добавить',
        'form': form,
        'space': None,
    })


@staff_member_required(login_url='/users/login/')
def admin_space_edit(request, space_id):
    space = get_object_or_404(Space, pk=space_id)
    form = SpaceForm(request.POST or None, request.FILES or None, instance=space)
    if request.method == 'POST':
        if form.is_valid():
            space = form.save()
            _create_space_photos(space, request.FILES.getlist('photos'))
            messages.success(request, 'Помещение обновлено.')
            return redirect('admin_spaces')
        messages.error(request, 'Проверьте данные формы.')
    return render(request, 'admin/space_form.html', {
        'action': 'Редактировать',
        'form': form,
        'space': space,
    })


@staff_member_required(login_url='/users/login/')
def admin_space_delete(request, space_id):
    space = get_object_or_404(Space, pk=space_id)
    if request.method == 'POST':
        space.delete()
        messages.success(request, 'Помещение удалено.')
    return redirect('admin_spaces')


@staff_member_required(login_url='/users/login/')
def admin_space_moderate(request, space_id):
    space = get_object_or_404(Space, pk=space_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        note = request.POST.get('moderation_note', '').strip()
        if action == 'approve':
            space.moderation_status = Space.MODERATION_APPROVED
            message_text = 'Помещение одобрено.'
        elif action == 'reject':
            if not note:
                messages.error(request, 'Укажите причину отклонения.')
                return redirect('admin_spaces')
            space.moderation_status = Space.MODERATION_REJECTED
            message_text = 'Помещение отклонено.'
        elif action == 'pending':
            space.moderation_status = Space.MODERATION_PENDING
            message_text = 'Помещение возвращено на модерацию.'
        elif action == 'revision_required':
            if not note:
                messages.error(request, 'Укажите, что нужно доработать.')
                return redirect('admin_spaces')
            space.moderation_status = Space.MODERATION_REVISION_REQUIRED
            message_text = 'Помещение отправлено на доработку.'
        else:
            messages.error(request, 'Некорректное действие модерации.')
            return redirect('admin_spaces')

        space.moderation_note = note
        space.save(update_fields=['moderation_status', 'moderation_note'])
        notify_space_moderation_changed(
            space=space,
            moderation_status=space.moderation_status,
            note=space.moderation_note,
            request=request,
        )
        messages.success(request, message_text)
    return redirect('admin_spaces')


def _create_space_photos(space, uploaded_photos):
    if SpacePhoto is None:
        return

    start_order = space.photos.count()
    for index, photo in enumerate(uploaded_photos):
        SpacePhoto.objects.create(
            space=space,
            image=photo,
            sort_order=start_order + index,
        )


# ---- Bookings ----

@staff_member_required(login_url='/users/login/')
def admin_bookings(request):
    booking_stats = {
        'total': 0,
        'pending': 0,
        'confirmed': 0,
        'cancelled': 0,
    }

    if Booking is None:
        bookings = []
        status_choices = []
    else:
        status = request.GET.get('status', '').strip()
        q      = request.GET.get('q', '').strip()
        date_from = request.GET.get('date_from', '').strip()
        date_to = request.GET.get('date_to', '').strip()

        bookings = Booking.objects.select_related('user', 'space').order_by('-created_at') \
            if hasattr(Booking, 'objects') else []

        status_counts = Booking.objects.values('status').annotate(total=Count('id'))
        booking_stats.update({
            row['status']: row['total']
            for row in status_counts
        })
        booking_stats['total'] = Booking.objects.count()

        if status:
            bookings = bookings.filter(status=status)
        if q:
            bookings = bookings.filter(
                Q(user__username__icontains=q) |
                Q(user__email__icontains=q) |
                Q(space__name__icontains=q)
            )
        if date_from:
            bookings = bookings.filter(check_in__date__gte=date_from)
        if date_to:
            bookings = bookings.filter(check_in__date__lte=date_to)

        status_choices = Booking.STATUS_CHOICES if hasattr(Booking, 'STATUS_CHOICES') else []

    return render(request, 'admin/bookings.html', {
        'bookings': bookings,
        'status_choices': status_choices,
        'booking_stats': booking_stats,
    })


@staff_member_required(login_url='/users/login/')
def admin_booking_status(request, booking_id):
    """Быстрое изменение статуса брони."""
    if Booking is None:
        return redirect('admin_bookings')

    booking = get_object_or_404(Booking, pk=booking_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = [value for value, _label in Booking.STATUS_CHOICES]
        if new_status in valid_statuses:
            booking.status = new_status
            booking.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Статус обновлён.')
        else:
            messages.error(request, 'Некорректный статус бронирования.')

    next_url = request.POST.get('next') or reverse('admin_bookings')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = reverse('admin_bookings')
    return redirect(next_url)


# ---- Payments ----

@staff_member_required(login_url='/users/login/')
def admin_payments(request):
    if Payment is None:
        payments = []
        status_choices = []
    else:
        status = request.GET.get('status', '').strip()
        payments = Payment.objects.select_related('booking').order_by('-created_at') \
            if hasattr(Payment, 'objects') else []
        if status:
            payments = payments.filter(status=status)
        status_choices = Payment.STATUS_CHOICES if hasattr(Payment, 'STATUS_CHOICES') else []
    return render(request, 'admin/payments.html', {
        'payments': payments,
        'status_choices': status_choices,
    })
