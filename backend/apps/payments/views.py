from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.bookings.models import Booking
from .models import Payment


def _demo_booking(booking_id=None):
    from types import SimpleNamespace

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
    payment = None
    if isinstance(booking, Booking):
        payment = Payment.objects.create_for_booking(booking)

    if request.method == 'POST':
        # Фантомная оплата: подтверждаем бронирование
        if booking.id and isinstance(booking, Booking):
            booking.status = Booking.STATUS_CONFIRMED
            booking.save(update_fields=['status', 'updated_at'])
            # Отправляем email об успешной оплате
            from apps.notifications.services import send_payment_success_email
            send_payment_success_email(booking)
        payment_query = f'&payment_id={payment.id}' if payment else ''
        return redirect(reverse('payments:success') + f'?booking_id={booking.id}{payment_query}')

    return render(request, 'payments/pay.html', {
        'booking': booking,
        'amount': booking.total_price,
        'payment': payment,
    })


def payment_success(request):
    booking_id = request.GET.get('booking_id')
    booking = _get_booking(booking_id)
    payment = _get_or_create_payment(booking, request.GET.get('payment_id'))
    if isinstance(payment, Payment) and payment.status != Payment.STATUS_SUCCESS:
        payment.status = Payment.STATUS_SUCCESS
        payment.save(update_fields=['status', 'updated_at'])

    return render(request, 'payments/success.html', {
        'booking': booking,
        'payment': payment,
    })


def payment_fail(request):
    booking_id = request.GET.get('booking_id')
    booking = _get_booking(booking_id)
    payment = _get_or_create_payment(booking, request.GET.get('payment_id'))
    if isinstance(payment, Payment) and payment.status != Payment.STATUS_FAIL:
        payment.status = Payment.STATUS_FAIL
        payment.save(update_fields=['status', 'updated_at'])
    retry_url = reverse('payments:pay_for_booking', args=[booking.id])

    return render(request, 'payments/fail.html', {
        'booking': booking,
        'payment': payment,
        'retry_url': retry_url,
        'error_message': request.GET.get('error'),
    })


def _get_or_create_payment(booking, payment_id=None):
    if isinstance(booking, Booking):
        if payment_id:
            return get_object_or_404(Payment, pk=payment_id, booking=booking)
        return Payment.objects.create_for_booking(booking)

    from types import SimpleNamespace

    return SimpleNamespace(
        id=payment_id or 1,
        booking=booking,
        amount=getattr(booking, 'total_price', 0),
        status='pending',
        status_label='Ожидает оплаты',
    )
