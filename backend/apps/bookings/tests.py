from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError

from datetime import date, timedelta

from apps.spaces.models import Space
from apps.bookings.models import Booking
from apps.bookings.services import (
    parse_booking_datetime,
    calculate_total_price,
    check_availability,
    create_booking,
)


User = get_user_model()



# apps/bookings/tests.py
class BookingModelTests(TestCase):
    def test_booking_creation(self):
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        space = Space.objects.create(
            name='Test Space',
            price_per_hour=1500,
            capacity=10,
            address='Test Address',
            moderation_status=Space.MODERATION_APPROVED,
        )
        
        # Убедитесь, что время в будущем и с точностью до минут
        check_in = timezone.now() + timedelta(days=1)
        check_in = check_in.replace(minute=0, second=0, microsecond=0)  # Ровный час
        check_out = check_in + timedelta(hours=3)
        
        booking = create_booking(
            user=user,
            space=space,
            check_in=check_in,
            check_out=check_out,
            guests=2,
        )
        
        # Проверяем цену
        expected_price = calculate_total_price(space, check_in, check_out)
        print(f"Expected: {expected_price}, Actual: {booking.total_price}")
        
        self.assertEqual(booking.total_price, expected_price)
        self.assertEqual(booking.total_price, 4500)

class BookingServiceTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='tester', password='pass')
        cls.space = Space.objects.create(
            name='Space Test',
            address='Addr',
            capacity=8,
            price_per_hour=1000,
            moderation_status=Space.MODERATION_APPROVED,
        )

    def test_calculate_total_price(self):
        check_in = timezone.now() + timedelta(days=1)
        check_out = check_in + timedelta(hours=2, minutes=30)
        price = calculate_total_price(self.space, check_in, check_out)
        self.assertEqual(price, 2500)

    def test_create_booking(self):
        check_in = timezone.now() + timedelta(days=5)
        check_out = check_in + timedelta(hours=4)

        booking = create_booking(
            user=self.user,
            space=self.space,
            check_in=check_in,
            check_out=check_out,
        )
        self.assertEqual(booking.total_price, 4000)
        self.assertEqual(booking.status, Booking.STATUS_PENDING)


class BookingViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='client', password='pass')
        self.space = Space.objects.create(
            name='Переговорная',
            address='ул. Ленина 1',
            capacity=10,
            price_per_hour=1200,
            moderation_status=Space.MODERATION_APPROVED,
        )
        self.client.force_login(self.user)

    def test_booking_create_view(self):
        future = timezone.now() + timedelta(days=3)
        response = self.client.post(
            reverse('bookings:create', args=[self.space.pk]),
            {
                'check_in': future.strftime('%Y-%m-%d %H:%M'),
                'check_out': (future + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M'),
                'guests': 3,
            }
        )
        self.assertEqual(response.status_code, 302)  # redirect to payment
        self.assertTrue(Booking.objects.filter(space=self.space).exists())