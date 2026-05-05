from types import SimpleNamespace

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.bookings.models import Booking


def _demo_booking(booking_id=None):
    return SimpleNamespace(
        id=booking_id or 1,
        space=SimpleNamespace(name='Конференц-зал Booking-Hub'),
        check_in=None,
        check_out=None,
        total_price=0,
    )


def _get_booking(booking_id=None):
    if booking_id:
        return get_object_or_404(Booking.objects.select_related('space', 'user'), pk=booking_id)
    return _demo_booking()


def payment_pay(request, booking_id=None):
    booking = _get_booking(booking_id)

    if request.method == 'POST':
        # Фантомная оплата: подтверждаем бронирование
        if booking.id and isinstance(booking, Booking):
            booking.status = Booking.STATUS_CONFIRMED
            booking.save(update_fields=['status', 'updated_at'])
            # Отправляем email об успешной оплате
            from apps.notifications.services import send_payment_success_email
            send_payment_success_email(booking)
        return redirect(reverse('payments:success') + f'?booking_id={booking.id}')

    return render(request, 'payments/pay.html', {
        'booking': booking,
        'amount': booking.total_price,
    })


def payment_success(request):
    booking_id = request.GET.get('booking_id')
    booking = _get_booking(booking_id)
    payment = SimpleNamespace(
        id=request.GET.get('payment_id') or 1,
        booking=booking,
        amount=request.GET.get('amount') or booking.total_price,
    )

    return render(request, 'payments/success.html', {
        'booking': booking,
        'payment': payment,
    })


def payment_fail(request):
    booking_id = request.GET.get('booking_id')
    booking = _get_booking(booking_id)
    payment = SimpleNamespace(
        booking=booking,
        amount=request.GET.get('amount') or booking.total_price,
    )
    retry_url = reverse('payments:pay_for_booking', args=[booking.id])

    return render(request, 'payments/fail.html', {
        'booking': booking,
        'payment': payment,
        'retry_url': retry_url,
        'error_message': request.GET.get('error'),
    })
