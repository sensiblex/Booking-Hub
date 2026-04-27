from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.spaces.models import Space


class Booking(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Ожидает'),
        (STATUS_CONFIRMED, 'Подтверждено'),
        (STATUS_CANCELLED, 'Отменено'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Пользователь',
    )
    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Помещение',
    )
    start_time = models.DateTimeField(verbose_name='Начало бронирования')
    end_time = models.DateTimeField(verbose_name='Окончание бронирования')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='Статус',
    )
    total_price = models.PositiveIntegerField(default=0, verbose_name='Сумма')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['space', 'start_time', 'end_time']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.space} — {self.user} ({self.start_time:%d.%m.%Y %H:%M})'

    @property
    def duration_hours(self):
        if not self.start_time or not self.end_time:
            return 0
        return (self.end_time - self.start_time).total_seconds() / 3600

    def clean(self):
        errors = {}

        if self.start_time and timezone.is_naive(self.start_time):
            self.start_time = timezone.make_aware(self.start_time)
        if self.end_time and timezone.is_naive(self.end_time):
            self.end_time = timezone.make_aware(self.end_time)

        if self.start_time and self.end_time and self.end_time <= self.start_time:
            errors['end_time'] = 'Окончание должно быть позже начала.'

        if self.start_time and self.start_time < timezone.now():
            errors['start_time'] = 'Нельзя создать бронирование в прошлом.'

        if errors:
            raise ValidationError(errors)
