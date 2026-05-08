from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_SPACE_SUBMITTED = 'space_submitted'
    TYPE_SPACE_RESUBMITTED = 'space_resubmitted'
    TYPE_SPACE_APPROVED = 'space_approved'
    TYPE_SPACE_REJECTED = 'space_rejected'
    TYPE_SPACE_REVISION_REQUIRED = 'space_revision_required'
    TYPE_BOOKING_REQUEST = 'booking_request'
    TYPE_BOOKING_APPROVED = 'booking_approved'
    TYPE_BOOKING_DECLINED = 'booking_declined'

    TYPE_CHOICES = [
        (TYPE_SPACE_SUBMITTED, 'Помещение отправлено на модерацию'),
        (TYPE_SPACE_RESUBMITTED, 'Помещение отправлено повторно'),
        (TYPE_SPACE_APPROVED, 'Помещение одобрено'),
        (TYPE_SPACE_REJECTED, 'Помещение отклонено'),
        (TYPE_SPACE_REVISION_REQUIRED, 'Помещение отправлено на доработку'),
        (TYPE_BOOKING_REQUEST, 'Новая заявка на аренду'),
        (TYPE_BOOKING_APPROVED, 'Аренда одобрена'),
        (TYPE_BOOKING_DECLINED, 'Аренда отклонена'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Пользователь',
    )
    type = models.CharField(max_length=40, choices=TYPE_CHOICES, verbose_name='Тип')
    title = models.CharField(max_length=160, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Сообщение')
    url = models.CharField(max_length=400, blank=True, verbose_name='Ссылка')
    is_read = models.BooleanField(default=False, db_index=True, verbose_name='Прочитано')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Создано')

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f'[{self.get_type_display()}] {self.user}: {self.title}'
