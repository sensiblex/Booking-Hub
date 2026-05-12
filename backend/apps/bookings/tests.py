from datetime import timedelta
from math import ceil
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.bookings.models import Booking
from apps.bookings.services import (
    calculate_total_price,
    check_availability,
    create_booking,
    get_overlapping_bookings,
    parse_booking_datetime,
)

from apps.bookings.factories import BookingFactory, SpaceFactory, UserFactory


class BookingModelTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.space = SpaceFactory()

    def test_str_representation(self):
        booking = BookingFactory(user=self.user, space=self.space)
        expected = f'{self.space} — {self.user} ({booking.check_in:%d.%m.%Y %H:%M})'
        self.assertEqual(str(booking), expected)

    def test_duration_hours(self):
        now = timezone.now()
        booking = BookingFactory.build(
            user=self.user, space=self.space,
            check_in=now, check_out=now + timedelta(hours=3),
        )
        self.assertEqual(booking.duration_hours, 3.0)

    def test_duration_hours_with_minutes(self):
        now = timezone.now()
        booking = BookingFactory.build(
            user=self.user, space=self.space,
            check_in=now, check_out=now + timedelta(minutes=90),
        )
        self.assertEqual(booking.duration_hours, 1.5)

    def test_duration_hours_zero_when_check_in_missing(self):
        booking = Booking(user=self.user, space=self.space, check_in=None, check_out=None)
        self.assertEqual(booking.duration_hours, 0)

    def test_duration_hours_zero_when_check_in_none(self):
        booking = Booking(user=self.user, space=self.space, check_in=None, check_out=timezone.now())
        self.assertEqual(booking.duration_hours, 0)

    def test_clean_makes_naive_check_in_aware(self):
        future_naive = (timezone.now() + timedelta(days=1)).replace(tzinfo=None)
        booking = Booking(
            user=self.user, space=self.space,
            check_in=future_naive,
            check_out=future_naive + timedelta(hours=2),
            total_price=2000,
        )
        booking.clean()
        self.assertTrue(timezone.is_aware(booking.check_in))
        self.assertTrue(timezone.is_aware(booking.check_out))

    def test_clean_raises_when_check_out_before_check_in(self):
        now = timezone.now()
        booking = Booking(
            user=self.user, space=self.space,
            check_in=now + timedelta(hours=2),
            check_out=now,
            total_price=2000,
        )
        with self.assertRaises(ValidationError) as ctx:
            booking.clean()
        self.assertIn('check_out', ctx.exception.error_dict)

    def test_clean_raises_when_check_in_in_past(self):
        past = timezone.now() - timedelta(days=1)
        booking = Booking(
            user=self.user, space=self.space,
            check_in=past,
            check_out=past + timedelta(hours=2),
            total_price=2000,
        )
        with self.assertRaises(ValidationError) as ctx:
            booking.clean()
        self.assertIn('check_in', ctx.exception.error_dict)

    def test_clean_passes_for_valid_booking(self):
        now = timezone.now()
        booking = Booking(
            user=self.user, space=self.space,
            check_in=now + timedelta(days=1),
            check_out=now + timedelta(days=1, hours=2),
            total_price=2000,
        )
        try:
            booking.clean()
        except ValidationError:
            self.fail('clean() raised ValidationError unexpectedly')

    def test_default_status_is_pending(self):
        booking = Booking(user=self.user, space=self.space)
        self.assertEqual(booking.status, Booking.STATUS_PENDING)

    def test_default_guests_is_one(self):
        booking = Booking(user=self.user, space=self.space)
        self.assertEqual(booking.guests, 1)

    def test_default_total_price_is_zero(self):
        booking = Booking(user=self.user, space=self.space)
        self.assertEqual(booking.total_price, 0)

    def test_ordering_newest_first(self):
        b1 = BookingFactory(user=self.user, space=self.space)
        b2 = BookingFactory(user=self.user, space=self.space)
        qs = Booking.objects.all()
        self.assertEqual(list(qs), [b2, b1])


class ParseBookingDatetimeTests(TestCase):
    def test_raises_error_for_empty_value(self):
        with self.assertRaises(ValidationError):
            parse_booking_datetime('')
        with self.assertRaises(ValidationError):
            parse_booking_datetime(None)

    def test_parses_iso_format_with_t(self):
        result = parse_booking_datetime('2025-06-15T14:30')
        expected = timezone.make_aware(timezone.datetime(2025, 6, 15, 14, 30))
        self.assertEqual(result, expected)

    def test_parses_iso_format_with_space(self):
        result = parse_booking_datetime('2025-06-15 14:30')
        expected = timezone.make_aware(timezone.datetime(2025, 6, 15, 14, 30))
        self.assertEqual(result, expected)

    def test_raises_error_for_invalid_format(self):
        with self.assertRaises(ValidationError):
            parse_booking_datetime('not-a-date')

    def test_returns_aware_datetime(self):
        result = parse_booking_datetime('2025-06-15 10:00')
        self.assertTrue(timezone.is_aware(result))

    def test_preserves_aware_datetime(self):
        now = timezone.now().replace(microsecond=0)
        result = parse_booking_datetime(now.isoformat())
        self.assertTrue(timezone.is_aware(result))
        self.assertEqual(result, now)


class CalculateTotalPriceTests(TestCase):
    def setUp(self):
        self.space = SpaceFactory(price_per_hour=1000)

    def test_full_hours(self):
        now = timezone.now()
        price = calculate_total_price(self.space, now, now + timedelta(hours=3))
        self.assertEqual(price, 3000)

    def test_ceil_partial_hour(self):
        now = timezone.now()
        price = calculate_total_price(self.space, now, now + timedelta(hours=1, minutes=1))
        expected = ceil((1 + 1/60) * 1000)
        self.assertEqual(price, expected)

    def test_zero_for_same_check_in_and_out(self):
        now = timezone.now()
        price = calculate_total_price(self.space, now, now)
        self.assertEqual(price, 0)

    def test_zero_for_negative_duration(self):
        now = timezone.now()
        price = calculate_total_price(self.space, now, now - timedelta(hours=1))
        self.assertEqual(price, 0)

    def test_different_price_per_hour(self):
        expensive = SpaceFactory(price_per_hour=2500)
        now = timezone.now()
        price = calculate_total_price(expensive, now, now + timedelta(hours=2))
        self.assertEqual(price, 5000)

    def test_ceil_30_minutes(self):
        now = timezone.now()
        price = calculate_total_price(self.space, now, now + timedelta(minutes=30))
        self.assertEqual(price, 500)

    def test_ceil_1_minute(self):
        now = timezone.now()
        price = calculate_total_price(self.space, now, now + timedelta(minutes=1))
        self.assertGreater(price, 0)
        self.assertLess(price, 1000)


class GetOverlappingBookingsTests(TestCase):
    def setUp(self):
        self.space = SpaceFactory()
        self.booking = BookingFactory(
            space=self.space,
            check_in=timezone.now() + timedelta(days=1),
            check_out=timezone.now() + timedelta(days=1, hours=2),
        )

    def test_finds_exact_overlap(self):
        overlaps = get_overlapping_bookings(
            self.space, self.booking.check_in, self.booking.check_out,
        )
        self.assertIn(self.booking, overlaps)

    def test_finds_partial_overlap_start(self):
        overlaps = get_overlapping_bookings(
            self.space,
            self.booking.check_in - timedelta(hours=1),
            self.booking.check_in + timedelta(hours=1),
        )
        self.assertIn(self.booking, overlaps)

    def test_finds_partial_overlap_end(self):
        overlaps = get_overlapping_bookings(
            self.space,
            self.booking.check_out - timedelta(hours=1),
            self.booking.check_out + timedelta(hours=1),
        )
        self.assertIn(self.booking, overlaps)

    def test_finds_containing_overlap(self):
        overlaps = get_overlapping_bookings(
            self.space,
            self.booking.check_in - timedelta(hours=1),
            self.booking.check_out + timedelta(hours=1),
        )
        self.assertIn(self.booking, overlaps)

    def test_no_overlap_before(self):
        overlaps = get_overlapping_bookings(
            self.space,
            self.booking.check_in - timedelta(days=3),
            self.booking.check_in - timedelta(days=3, hours=-2),
        )
        self.assertNotIn(self.booking, overlaps)

    def test_no_overlap_after(self):
        overlaps = get_overlapping_bookings(
            self.space,
            self.booking.check_out + timedelta(hours=1),
            self.booking.check_out + timedelta(hours=3),
        )
        self.assertNotIn(self.booking, overlaps)

    def test_exclude_booking_id(self):
        overlaps = get_overlapping_bookings(
            self.space, self.booking.check_in, self.booking.check_out,
            exclude_booking_id=self.booking.pk,
        )
        self.assertNotIn(self.booking, overlaps)

    def test_ignores_cancelled_and_completed(self):
        cancelled = BookingFactory(
            space=self.space, status=Booking.STATUS_CANCELLED,
            check_in=timezone.now() + timedelta(days=1),
            check_out=timezone.now() + timedelta(days=1, hours=2),
        )
        completed = BookingFactory(
            space=self.space, status=Booking.STATUS_COMPLETED,
            check_in=timezone.now() + timedelta(days=1),
            check_out=timezone.now() + timedelta(days=1, hours=2),
        )
        overlaps = get_overlapping_bookings(
            self.space,
            timezone.now() + timedelta(days=1),
            timezone.now() + timedelta(days=1, hours=2),
        )
        self.assertNotIn(cancelled, overlaps)
        self.assertNotIn(completed, overlaps)

    def test_only_same_space(self):
        other_space = SpaceFactory()
        other_booking = BookingFactory(
            space=other_space,
            check_in=timezone.now() + timedelta(days=1),
            check_out=timezone.now() + timedelta(days=1, hours=2),
        )
        overlaps = get_overlapping_bookings(
            self.space, other_booking.check_in, other_booking.check_out,
        )
        self.assertNotIn(other_booking, overlaps)

    def test_empty_when_no_bookings(self):
        SpaceFactory()
        overlaps = get_overlapping_bookings(
            SpaceFactory(),
            timezone.now() + timedelta(days=1),
            timezone.now() + timedelta(days=1, hours=2),
        )
        self.assertFalse(overlaps.exists())


class CheckAvailabilityTests(TestCase):
    def setUp(self):
        self.space = SpaceFactory()
        self.future = timezone.now() + timedelta(days=1)
        self.future_end = self.future + timedelta(hours=2)

    def test_available_when_no_overlaps(self):
        result = check_availability(self.space, self.future, self.future_end)
        self.assertTrue(result)

    def test_raises_when_check_out_before_check_in(self):
        with self.assertRaises(ValidationError) as ctx:
            check_availability(self.space, self.future_end, self.future)
        self.assertIn('Окончание должно быть позже начала', str(ctx.exception))

    def test_raises_when_check_in_in_past(self):
        past = timezone.now() - timedelta(days=1)
        with self.assertRaises(ValidationError) as ctx:
            check_availability(self.space, past, past + timedelta(hours=2))
        self.assertIn('Нельзя создать бронирование в прошлом', str(ctx.exception))

    def test_raises_when_overlap_exists(self):
        BookingFactory(space=self.space, check_in=self.future, check_out=self.future_end)
        with self.assertRaises(ValidationError) as ctx:
            check_availability(self.space, self.future, self.future_end)
        self.assertIn('уже занят', str(ctx.exception))

    def test_allows_excluding_own_overlap(self):
        booking = BookingFactory(space=self.space, check_in=self.future, check_out=self.future_end)
        result = check_availability(
            self.space, self.future, self.future_end,
            exclude_booking_id=booking.pk,
        )
        self.assertTrue(result)

    def test_allows_when_overlap_is_cancelled(self):
        BookingFactory(
            space=self.space, status=Booking.STATUS_CANCELLED,
            check_in=self.future, check_out=self.future_end,
        )
        result = check_availability(self.space, self.future, self.future_end)
        self.assertTrue(result)


class CreateBookingTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.space = SpaceFactory(price_per_hour=1000)
        self.future = timezone.now() + timedelta(days=1)
        self.future_end = self.future + timedelta(hours=3)

    def test_creates_booking_with_calculated_price(self):
        booking = create_booking(
            user=self.user, space=self.space,
            check_in=self.future, check_out=self.future_end,
        )
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.space, self.space)
        self.assertEqual(booking.check_in, self.future)
        self.assertEqual(booking.check_out, self.future_end)
        self.assertEqual(booking.total_price, 3000)
        self.assertEqual(booking.guests, 1)
        self.assertEqual(booking.status, Booking.STATUS_PENDING)
        self.assertEqual(booking.special_requests, '')

    def test_creates_booking_with_custom_guests_and_requests(self):
        booking = create_booking(
            user=self.user, space=self.space,
            check_in=self.future, check_out=self.future_end,
            guests=5, special_requests='Нужен проектор',
        )
        self.assertEqual(booking.guests, 5)
        self.assertEqual(booking.special_requests, 'Нужен проектор')

    def test_raises_on_overlap(self):
        create_booking(
            user=self.user, space=self.space,
            check_in=self.future, check_out=self.future_end,
        )
        with self.assertRaises(ValidationError):
            create_booking(
                user=self.user, space=self.space,
                check_in=self.future, check_out=self.future_end,
            )

    def test_saves_to_database(self):
        booking = create_booking(
            user=self.user, space=self.space,
            check_in=self.future, check_out=self.future_end,
        )
        self.assertIsNotNone(booking.pk)
        self.assertEqual(Booking.objects.count(), 1)

    def test_raises_on_past_check_in(self):
        past = timezone.now() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            create_booking(
                user=self.user, space=self.space,
                check_in=past, check_out=past + timedelta(hours=2),
            )

    def test_raises_on_inverted_dates(self):
        with self.assertRaises(ValidationError):
            create_booking(
                user=self.user, space=self.space,
                check_in=self.future_end, check_out=self.future,
            )

    def test_different_spaces_no_overlap(self):
        other_space = SpaceFactory(price_per_hour=500)
        create_booking(
            user=self.user, space=self.space,
            check_in=self.future, check_out=self.future_end,
        )
        booking2 = create_booking(
            user=self.user, space=other_space,
            check_in=self.future, check_out=self.future_end,
        )
        self.assertIsNotNone(booking2.pk)


class BookingStatusChangedSignalTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.space = SpaceFactory()
        self.booking = BookingFactory(
            user=self.user, space=self.space, status=Booking.STATUS_PENDING,
        )

    @patch('apps.bookings.signals.send_payment_success_email')
    def test_signal_ignores_creation(self, mock_email):
        BookingFactory(user=self.user, space=self.space)
        mock_email.assert_not_called()

    @patch('apps.bookings.signals.send_booking_cancellation_email')
    def test_signal_ignores_save_without_status_change(self, mock_email):
        self.booking.save()
        mock_email.assert_not_called()
