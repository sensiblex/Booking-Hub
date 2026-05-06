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
    check_in = models.DateTimeField(verbose_name='Заезд')
    check_out = models.DateTimeField(verbose_name='Выезд')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='Статус',
    )
    total_price = models.PositiveIntegerField(default=0, verbose_name='Сумма')
    guests = models.PositiveIntegerField(default=1, verbose_name='Количество гостей')
    special_requests = models.TextField(blank=True, verbose_name='Особые пожелания')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['space', 'check_in', 'check_out']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.space} — {self.user} ({self.check_in:%d.%m.%Y %H:%M})'

    @property
    def duration_hours(self):
        if not self.check_in or not self.check_out:
            return 0
        return (self.check_out - self.check_in).total_seconds() / 3600

    def clean(self):
        errors = {}

        if self.check_in and timezone.is_naive(self.check_in):
            self.check_in = timezone.make_aware(self.check_in)
        if self.check_out and timezone.is_naive(self.check_out):
            self.check_out = timezone.make_aware(self.check_out)

        if self.check_in and self.check_out and self.check_out <= self.check_in:
            errors['check_out'] = 'Окончание должно быть позже начала.'

        if self.check_in and self.check_in < timezone.now():
            errors['check_in'] = 'Нельзя создать бронирование в прошлом.'

        if errors:
            raise ValidationError(errors)
