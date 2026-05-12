from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.bookings.models import Booking
from apps.notifications.models import Notification
from apps.payments.models import Payment
from apps.spaces.models import Space


class PaymentStatusTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='client',
            password='pass',
            role='client',
        )
        self.landlord = User.objects.create_user(
            username='landlord',
            password='pass',
            role='client',
        )
        self.space = Space.objects.create(
            name='Переговорная Ньютон',
            address='ул. Пушкина, 5',
            capacity=8,
            price_per_hour=900,
            submitted_by=self.landlord,
        )
        self.booking = Booking.objects.create(
            user=self.user,
            space=self.space,
            check_in=timezone.now() + timedelta(days=1),
            check_out=timezone.now() + timedelta(days=1, hours=2),
            total_price=1800,
        )

    def test_payment_created_as_pending_for_booking(self):
        payment = Payment.objects.create_for_booking(self.booking)

        self.assertEqual(payment.status, Payment.STATUS_PENDING)
        self.assertEqual(payment.status_label, 'Ожидает оплаты')

    def test_payment_sets_booking_awaiting_confirmation(self):
        Payment.objects.create_for_booking(self.booking)

        response = self.client.post(
            reverse('payments:pay_for_booking', args=[self.booking.id]),
        )

        self.assertEqual(response.status_code, 302)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_AWAITING_CONFIRMATION)
        self.assertTrue(
            Notification.objects.filter(
                user=self.landlord,
                type=Notification.TYPE_BOOKING_REQUEST,
            ).exists()
        )

    def test_success_page_marks_booking_payment_success(self):
        payment = Payment.objects.create_for_booking(self.booking)

        response = self.client.get(
            reverse('payments:success'),
            {'booking_id': self.booking.id, 'payment_id': payment.id},
        )

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.STATUS_SUCCESS)

    def test_fail_page_marks_booking_payment_failed(self):
        payment = Payment.objects.create_for_booking(self.booking)

        response = self.client.get(
            reverse('payments:fail'),
            {'booking_id': self.booking.id, 'payment_id': payment.id},
        )

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.STATUS_FAIL)

    def test_booking_history_shows_payment_status_badges(self):
        Payment.objects.create_for_booking(self.booking)
        self.client.force_login(self.user)

        response = self.client.get(reverse('bookings:history'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ожидает оплаты')
        self.assertContains(response, 'payment-status-pending')

    def test_booking_history_treats_missing_payment_as_pending(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('bookings:history'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ожидает оплаты')
        self.assertContains(response, 'payment-status-pending')

    def test_booking_history_shows_success_and_fail_payment_badges(self):
        paid_booking = self.booking
        failed_booking = Booking.objects.create(
            user=self.user,
            space=self.space,
            check_in=timezone.now() + timedelta(days=2),
            check_out=timezone.now() + timedelta(days=2, hours=2),
            total_price=1800,
        )
        Payment.objects.create(
            booking=paid_booking,
            amount=paid_booking.total_price,
            status=Payment.STATUS_SUCCESS,
        )
        Payment.objects.create(
            booking=failed_booking,
            amount=failed_booking.total_price,
            status=Payment.STATUS_FAIL,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('bookings:history'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Оплачено')
        self.assertContains(response, 'payment-status-success')
        self.assertContains(response, 'Ошибка оплаты')
        self.assertContains(response, 'payment-status-fail')
