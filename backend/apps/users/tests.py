from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.bookings.models import Booking
from apps.payments.models import Payment
from apps.spaces.models import Space


class AdminDashboardApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            username='admin_dashboard',
            password='pass',
            role='administrator',
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username='client_dashboard',
            password='pass',
            role='client',
            is_staff=False,
        )
        User.objects.create_user(
            username='manager_dashboard',
            password='pass',
            role='manager',
            is_staff=True,
        )

        self.space_a = Space.objects.create(
            name='Переговорная Альфа',
            address='ул. Тестовая, 1',
            capacity=8,
            price_per_hour=900,
        )
        self.space_b = Space.objects.create(
            name='Переговорная Бета',
            address='ул. Тестовая, 2',
            capacity=12,
            price_per_hour=1200,
        )

        now = timezone.now()
        booking_recent_1 = Booking.objects.create(
            user=self.regular_user,
            space=self.space_a,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=2),
            total_price=1800,
        )
        booking_recent_2 = Booking.objects.create(
            user=self.regular_user,
            space=self.space_a,
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=2, hours=3),
            total_price=2700,
            status=Booking.STATUS_CONFIRMED,
        )
        booking_old = Booking.objects.create(
            user=self.regular_user,
            space=self.space_b,
            start_time=now + timedelta(days=3),
            end_time=now + timedelta(days=3, hours=1),
            total_price=1200,
            status=Booking.STATUS_CANCELLED,
        )
        Booking.objects.filter(pk=booking_old.pk).update(created_at=now - timedelta(days=40))

        Payment.objects.create(booking=booking_recent_1, amount=1000, status=Payment.STATUS_PENDING)
        Payment.objects.create(booking=booking_recent_2, amount=3000, status=Payment.STATUS_FAIL)
        Payment.objects.create(booking=booking_old, amount=5000, status=Payment.STATUS_SUCCESS)

        self.url = reverse('admin_dashboard_api')

    def test_api_requires_staff_access(self):
        self.client.force_login(self.regular_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/users/login/', response.url)

    def test_api_returns_expected_contract_for_staff(self):
        self.client.force_login(self.staff)

        response = self.client.get(self.url, {'period': 30})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('users_by_role', payload)
        self.assertIn('bookings_by_day', payload)
        self.assertIn('bookings_by_week', payload)
        self.assertIn('revenue', payload)
        self.assertIn('top_spaces', payload)
        self.assertIn('meta', payload)
        self.assertEqual(payload['meta']['period_days'], 30)
        self.assertEqual(payload['revenue']['currency'], 'RUB')
        self.assertEqual(payload['revenue']['period_total'], 4000)

        role_counts = {row['role']: row['count'] for row in payload['users_by_role']}
        self.assertEqual(role_counts['administrator'], 1)
        self.assertEqual(role_counts['client'], 1)
        self.assertEqual(role_counts['manager'], 1)

        self.assertTrue(payload['bookings_by_day'])
        self.assertTrue(payload['bookings_by_week'])
        self.assertEqual(payload['top_spaces'][0]['space_name'], 'Переговорная Альфа')
        self.assertEqual(payload['top_spaces'][0]['bookings_count'], 2)

    def test_period_filter_changes_aggregates(self):
        self.client.force_login(self.staff)

        response_30 = self.client.get(self.url, {'period': 30})
        response_365 = self.client.get(self.url, {'period': 365})

        payload_30 = response_30.json()
        payload_365 = response_365.json()
        self.assertEqual(payload_30['revenue']['period_total'], 4000)
        self.assertEqual(payload_365['revenue']['period_total'], 9000)
        self.assertEqual(len(payload_30['bookings_by_day']), 2)
        self.assertEqual(len(payload_365['bookings_by_day']), 3)
