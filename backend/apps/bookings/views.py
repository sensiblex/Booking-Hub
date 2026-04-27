from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from apps.spaces.models import Space

from .models import Booking
from .services import create_booking, parse_booking_datetime


def _can_manage_bookings(user):
    return (
        user.is_staff
        or getattr(user, 'role', None) in ('manager', 'administrator')
    )


@login_required(login_url='/users/login/')
def booking_create(request, space_id):
    space = get_object_or_404(Space, id=space_id)

    if request.method == 'POST':
        try:
            start_time = parse_booking_datetime(request.POST.get('start_time'))
            end_time = parse_booking_datetime(request.POST.get('end_time'))
            booking = create_booking(
                user=request.user,
                space=space,
                start_time=start_time,
                end_time=end_time,
                comment=request.POST.get('comment', '').strip(),
            )
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
        else:
            messages.success(request, 'Бронирование создано. Перейдите к оплате.')
            return redirect('payments:pay_for_booking', booking_id=booking.id)

    return render(request, 'bookings/create.html', {'space': space})


@login_required(login_url='/users/login/')
def booking_history(request):
    bookings = (
        Booking.objects
        .select_related('space')
        .filter(user=request.user)
        .order_by('-start_time')
    )
    return render(request, 'bookings/history.html', {'bookings': bookings})


@login_required(login_url='/users/login/')
def manager_bookings(request):
    if not _can_manage_bookings(request.user):
        messages.error(request, 'Доступ запрещён.')
        return redirect('bookings:history')

    bookings = (
        Booking.objects
        .select_related('user', 'space')
        .order_by('-start_time')
    )
    return render(request, 'manager/bookings.html', {
        'bookings': bookings,
        'status_choices': Booking.STATUS_CHOICES,
    })


@login_required(login_url='/users/login/')
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.user != request.user and not _can_manage_bookings(request.user):
        messages.error(request, 'Доступ запрещён.')
        return redirect('bookings:history')

    if request.method == 'POST':
        if booking.status == Booking.STATUS_CANCELLED:
            messages.info(request, 'Бронирование уже отменено.')
        else:
            booking.status = Booking.STATUS_CANCELLED
            booking.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Бронирование отменено.')

    if _can_manage_bookings(request.user) and booking.user != request.user:
        return redirect('bookings:manager_bookings')
    return redirect('bookings:history')


@login_required(login_url='/users/login/')
def update_booking_status(request, booking_id):
    if not _can_manage_bookings(request.user):
        messages.error(request, 'Доступ запрещён.')
        return redirect('bookings:history')

    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = [status for status, _label in Booking.STATUS_CHOICES]
        if new_status in valid_statuses:
            booking.status = new_status
            booking.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Статус бронирования обновлён.')
        else:
            messages.error(request, 'Некорректный статус бронирования.')

    return redirect('bookings:manager_bookings')
