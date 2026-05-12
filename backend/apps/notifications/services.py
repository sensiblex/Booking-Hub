from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

from .models import Notification


def create_notification(user, notification_type, title, message, url='', request=None):
    if user is None:
        return None

    notification = Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        message=message,
        url=url,
    )

    if request is not None:
        queue = request.session.get('fresh_notification_ids', [])
        queue.append(notification.id)
        request.session['fresh_notification_ids'] = queue[-10:]

    return notification


def notify_space_moderation_changed(space, moderation_status, note='', request=None):
    owner = space.submitted_by
    if owner is None:
        return None

    if moderation_status == 'approved':
        notification_type = Notification.TYPE_SPACE_APPROVED
        title = 'Помещение одобрено'
        message = f'Помещение "{space.name}" прошло модерацию и опубликовано.'
    elif moderation_status == 'rejected':
        notification_type = Notification.TYPE_SPACE_REJECTED
        title = 'Помещение отклонено'
        message = f'Заявка по помещению "{space.name}" отклонена.'
        if note:
            message = f'{message} Причина: {note}'
    elif moderation_status == 'revision_required':
        notification_type = Notification.TYPE_SPACE_REVISION_REQUIRED
        title = 'Помещение отправлено на доработку'
        message = f'Заявку по помещению "{space.name}" нужно доработать.'
        if note:
            message = f'{message} Комментарий модератора: {note}'
    elif moderation_status == 'pending':
        notification_type = Notification.TYPE_SPACE_RESUBMITTED
        title = 'Помещение отправлено на повторную модерацию'
        message = f'Помещение "{space.name}" отправлено на повторную проверку.'
    else:
        return None

    return create_notification(
        user=owner,
        notification_type=notification_type,
        title=title,
        message=message,
        url=reverse('spaces:my_spaces'),
        request=request,
    )


def notify_landlord_new_booking_request(booking, request=None):
    landlord = booking.space.submitted_by
    if landlord is None or landlord == booking.user:
        return None

    return create_notification(
        user=landlord,
        notification_type=Notification.TYPE_BOOKING_REQUEST,
        title='Новая заявка на аренду',
        message=(
            f'Новая заявка на помещение "{booking.space.name}" '
            f'от пользователя {booking.user.username}.'
        ),
        url=reverse('spaces:my_spaces'),
        request=request,
    )


def notify_tenant_booking_decision(booking, approved, request=None):
    return create_notification(
        user=booking.user,
        notification_type=(
            Notification.TYPE_BOOKING_APPROVED
            if approved
            else Notification.TYPE_BOOKING_DECLINED
        ),
        title='Заявка на аренду одобрена' if approved else 'Заявка на аренду отклонена',
        message=(
            f'По помещению "{booking.space.name}" принято решение: '
            f'{"одобрено" if approved else "отклонено"}.'
        ),
        url=reverse('bookings:history'),
        request=request,
    )


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
