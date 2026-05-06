from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta

from apps.spaces.models import Space

from .models import Booking
from .services import (
    calculate_total_price,
    check_availability,
    create_booking,
    parse_booking_datetime,
)


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
            check_in = parse_booking_datetime(request.POST.get('check_in'))
            check_out = parse_booking_datetime(request.POST.get('check_out'))
            booking = create_booking(
                user=request.user,
                space=space,
                check_in=check_in,
                check_out=check_out,
                guests=request.POST.get('guests', 1),
                special_requests=request.POST.get('special_requests', '').strip(),
            )
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
        else:
            messages.success(request, 'Бронирование создано. Перейдите к оплате.')
            return redirect('payments:pay_for_booking', booking_id=booking.id)

    return render(request, 'bookings/create.html', {'space': space})


def check_booking_availability(request):
    try:
        space = get_object_or_404(Space, id=request.GET.get('space_id'))
        check_in = parse_booking_datetime(request.GET.get('check_in'))
        check_out = parse_booking_datetime(request.GET.get('check_out'))
        check_availability(space, check_in, check_out)
    except ValidationError as exc:
        return JsonResponse({
            'available': False,
            'message': ' '.join(exc.messages),
        }, status=400)
    except Http404:
        return JsonResponse({
            'available': False,
            'message': 'Помещение не найдено.',
        }, status=404)

    return JsonResponse({
        'available': True,
        'message': 'Слот свободен.',
        'total_price': calculate_total_price(space, check_in, check_out),
    })


@login_required(login_url='/users/login/')
def booking_history(request):
    cutoff = timezone.now() - timedelta(days=30)
    Booking.objects.filter(
        user=request.user,
        status__in=[Booking.STATUS_CANCELLED, Booking.STATUS_COMPLETED],
        check_out__lt=cutoff,
    ).delete()
    Booking.objects.filter(
        user=request.user,
        status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_AWAITING_CONFIRMATION],
        check_out__lt=timezone.now(),
    ).update(status=Booking.STATUS_COMPLETED)

    sort = request.GET.get('sort', 'created_desc')
    order_map = {
        'created_desc': '-created_at',
        'created_asc': 'created_at',
        'date_asc': 'check_in',
        'date_desc': '-check_in',
    }
    order = order_map.get(sort, '-created_at')

    bookings = (
        Booking.objects
        .select_related('space', 'payment')
        .filter(user=request.user)
        .order_by(order)
    )
    return render(request, 'bookings/history.html', {'bookings': bookings, 'current_sort': sort})


@login_required(login_url='/users/login/')
def clear_booking_history(request):
    if request.method == 'POST':
        deleted, _ = Booking.objects.filter(
            user=request.user,
            status__in=[Booking.STATUS_CANCELLED, Booking.STATUS_CONFIRMED],
            check_out__lt=timezone.now(),
        ).delete()
        messages.success(request, f'Удалено {deleted} завершённых бронирований.')
    return redirect('bookings:history')


@login_required(login_url='/users/login/')
def manager_bookings(request):
    if not _can_manage_bookings(request.user):
        messages.error(request, 'Доступ запрещён.')
        return redirect('bookings:history')

    bookings = (
        Booking.objects
        .select_related('user', 'space')
        .order_by('-check_in')
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
