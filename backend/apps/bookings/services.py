from datetime import datetime
from math import ceil

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Booking


DATETIME_INPUT_FORMATS = (
    '%Y-%m-%d %H:%M',
    '%Y-%m-%dT%H:%M',
)


def parse_booking_datetime(value):
    if not value:
        raise ValidationError('Укажите дату и время.')

    parsed = parse_datetime(value)
    if parsed is None:
        for fmt in DATETIME_INPUT_FORMATS:
            try:
                parsed = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue

    if parsed is None:
        raise ValidationError('Некорректный формат даты и времени.')

    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)
    return parsed


def calculate_total_price(space, start_time, end_time):
    duration_hours = (end_time - start_time).total_seconds() / 3600
    return max(0, ceil(duration_hours * space.price_per_hour))


def get_overlapping_bookings(space, start_time, end_time, exclude_booking_id=None):
    bookings = Booking.objects.filter(
        space=space,
        status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED],
        start_time__lt=end_time,
        end_time__gt=start_time,
    )
    if exclude_booking_id:
        bookings = bookings.exclude(pk=exclude_booking_id)
    return bookings


def check_availability(space, start_time, end_time, exclude_booking_id=None):
    if end_time <= start_time:
        raise ValidationError('Окончание должно быть позже начала.')

    if start_time < timezone.now():
        raise ValidationError('Нельзя создать бронирование в прошлом.')

    if get_overlapping_bookings(space, start_time, end_time, exclude_booking_id).exists():
        raise ValidationError('Выбранный интервал уже занят.')

    return True


def create_booking(user, space, start_time, end_time, comment=''):
    check_availability(space, start_time, end_time)
    booking = Booking(
        user=user,
        space=space,
        start_time=start_time,
        end_time=end_time,
        comment=comment,
        total_price=calculate_total_price(space, start_time, end_time),
    )
    booking.full_clean()
    booking.save()
    return booking
