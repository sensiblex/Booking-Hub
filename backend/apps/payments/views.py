from types import SimpleNamespace

from django.shortcuts import redirect, render
from django.urls import reverse


def _demo_booking(booking_id=None):
    return SimpleNamespace(
        id=booking_id or 1,
        space=SimpleNamespace(name='Конференц-зал Booking-Hub'),
        start_time=None,
        end_time=None,
        total_price=0,
    )


def payment_pay(request, booking_id=None):
    booking = _demo_booking(booking_id)

    if request.method == 'POST':
        return redirect(reverse('payments:success') + f'?booking_id={booking.id}')

    return render(request, 'payments/pay.html', {
        'booking': booking,
        'amount': booking.total_price,
    })


def payment_success(request):
    booking_id = request.GET.get('booking_id')
    booking = _demo_booking(booking_id)
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
    booking = _demo_booking(booking_id)
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
