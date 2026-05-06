from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from apps.bookings.models import Booking
from apps.notifications.services import (
    send_booking_confirmation_email,
    send_booking_cancellation_email,
    send_payment_success_email,
)


@receiver(post_save, sender=Booking)
def booking_status_changed(sender, instance, created, **kwargs):
    """Триггер на изменение статуса бронирования"""
    if created:
        return
    
    if not instance.pk:
        return
    
    try:
        old_booking = Booking.objects.get(pk=instance.pk)
    except Booking.DoesNotExist:
        return
    
    if old_booking.status != instance.status:
        if instance.status == Booking.STATUS_CONFIRMED:
            if settings.DEBUG:
                print(f'Booking #{instance.id} confirmed, sending email...')
            send_booking_confirmation_email(instance)
        
        elif instance.status == Booking.STATUS_CANCELLED:
            if settings.DEBUG:
                print(f'Booking #{instance.id} cancelled, sending email...')
            send_booking_cancellation_email(instance)


def payment_completed(sender, booking, **kwargs):
    """Триггер на успешную оплату"""
    if settings.DEBUG:
        print(f'Payment for booking #{booking.id} completed, sending email...')
    send_payment_success_email(booking)
