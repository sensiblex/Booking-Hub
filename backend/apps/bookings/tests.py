from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.spaces.models import Space, Category
from .models import Booking
from .services import (
    parse_booking_datetime,
    calculate_total_price,
    check_availability,
    create_booking,
    get_overlapping_bookings,
)


User = get_user_model()


class BookingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='renter', password='pass')
        self.space = Space.objects.create(
            name='Тестовая переговорная',
            address='ул. Тестовая, 10',
            capacity=10,
            price_per_hour=1500,
            moderation_status=Space.MODERATION_APPROVED,
        )

    def test_booking_creation(self):
        booking = Booking.objects.create(
            user=self.user,
            space=self.space,
            check_in=timezone.now() + timedelta(days=1),
            check_out=timezone.now() + timedelta(days=1, hours=2),
            guests=4,
            special_requests='С проектором',
        )
        self.assertEqual(booking.status, Booking.STATUS_PENDING)
        self.assertEqual(booking.total_price, 3000)
        self.assertTrue(str(booking).startswith('Тестовая переговорная'))

    def test_clean_method_validation(self):
        booking = Booking(
            user=self.user,
            space=self.space,
            check_in=timezone.now() + timedelta(hours=1),
            check_out=timezone.now() + timedelta(minutes=30),  # check_out раньше check_in
        )
        with self.assertRaises(ValidationError):
            booking.full_clean()


class BookingServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')
        self.space = Space.objects.create(
            name='Space', address='Addr', capacity=8, price_per_hour=1000,
            moderation_status=Space.MODERATION_APPROVED
        )

    def test_parse_booking_datetime(self):
        dt = parse_booking_datetime("2026-05-20 14:30")
        self.assertEqual(dt.hour, 14)
        self.assertEqual(dt.minute, 30)

        with self.assertRaises(ValidationError):
            parse_booking_datetime("")

    def test_calculate_total_price(self):
        check_in = timezone.now() + timedelta(days=1)
        check_out = check_in + timedelta(hours=3, minutes=30)
        price = calculate_total_price(self.space, check_in, check_out)
        self.assertEqual(price, 3500)  # 3.5 часа * 1000

    def test_check_availability(self):
        # Создаём пересекающееся бронирование
        existing = Booking.objects.create(
            user=self.user,
            space=self.space,
            check_in=timezone.now() + timedelta(days=2),
            check_out=timezone.now() + timedelta(days=2, hours=3),
            status=Booking.STATUS_CONFIRMED,
        )

        with self.assertRaises(ValidationError):
            check_availability(
                self.space,
                existing.check_in + timedelta(hours=1),
                existing.check_out - timedelta(hours=1)
            )

    def test_create_booking_success(self):
        check_in = timezone.now() + timedelta(days=5)
        check_out = check_in + timedelta(hours=4)

        booking = create_booking(
            user=self.user,
            space=self.space,
            check_in=check_in,
            check_out=check_out,
            guests=6,
            special_requests='Тест'
        )

        self.assertEqual(booking.total_price, 4000)
        self.assertEqual(booking.status, Booking.STATUS_PENDING)


class BookingViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='client', password='pass')
        self.space = Space.objects.create(
            name='Переговорная', address='ул. Ленина', capacity=10,
            price_per_hour=1200, moderation_status=Space.MODERATION_APPROVED
        )
        self.client.force_login(self.user)

    def test_booking_create_view(self):
        check_in = timezone.now() + timedelta(days=3)
        check_out = check_in + timedelta(hours=2)

        response = self.client.post(reverse('bookings:create', args=[self.space.id]), {
            'check_in': check_in.strftime('%Y-%m-%d %H:%M'),
            'check_out': check_out.strftime('%Y-%m-%d %H:%M'),
            'guests': 3,
        })

        self.assertRedirects(response, reverse('payments:pay_for_booking', args=[1]))
        self.assertTrue(Booking.objects.filter(space=self.space).exists())

    def test_check_availability_api(self):
        check_in = timezone.now() + timedelta(days=10)
        check_out = check_in + timedelta(hours=2)

        response = self.client.get(reverse('bookings:check_availability'), {
            'space_id': self.space.id,
            'check_in': check_in.strftime('%Y-%m-%d %H:%M'),
            'check_out': check_out.strftime('%Y-%m-%d %H:%M'),
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['available'])
        self.assertEqual(data['total_price'], 2400)

    def test_cancel_booking(self):
        booking = Booking.objects.create(
            user=self.user,
            space=self.space,
            check_in=timezone.now() + timedelta(days=5),
            check_out=timezone.now() + timedelta(days=5, hours=3),
            status=Booking.STATUS_AWAITING_CONFIRMATION,
        )

        response = self.client.post(reverse('bookings:cancel', args=[booking.id]))
        self.assertRedirects(response, reverse('bookings:history'))

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_CANCELLED)


class ManagerBookingTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username='manager', password='pass', role='manager')
        self.client.force_login(self.manager)

    def test_manager_can_access_bookings(self):
        response = self.client.get(reverse('bookings:manager_bookings'))
        self.assertEqual(response.status_code, 200)
