from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_booking_confirmation_email(booking):
    """Отправка email о подтверждении бронирования"""
    subject = f'Бронирование #{booking.id} подтверждено'
    
    context = {
        'booking': booking,
        'user': booking.user,
        'space': booking.space,
    }
    
    html_message = render_to_string('emails/booking_confirmed.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_booking_cancellation_email(booking):
    """Отправка email об отмене бронирования"""
    subject = f'Бронирование #{booking.id} отменено'
    
    context = {
        'booking': booking,
        'user': booking.user,
        'space': booking.space,
    }
    
    html_message = render_to_string('emails/booking_cancelled.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_payment_success_email(booking):
    """Отправка email об успешной оплате"""
    subject = f'Оплата бронирования #{booking.id} прошла успешно'
    
    context = {
        'booking': booking,
        'user': booking.user,
        'space': booking.space,
        'amount': booking.total_price,
    }
    
    html_message = render_to_string('emails/payment_success.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.user.email],
        html_message=html_message,
        fail_silently=False,
    )
