from django.db import models


class PaymentQuerySet(models.QuerySet):
    def create_for_booking(self, booking):
        payment, _created = self.get_or_create(
            booking=booking,
            defaults={
                'amount': booking.total_price,
                'status': Payment.STATUS_PENDING,
            },
        )
        return payment


class Payment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAIL = 'fail'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Ожидает оплаты'),
        (STATUS_SUCCESS, 'Оплачено'),
        (STATUS_FAIL, 'Ошибка оплаты'),
    ]

    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name='Бронирование',
    )
    amount = models.PositiveIntegerField(verbose_name='Сумма')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='Статус',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    objects = PaymentQuerySet.as_manager()

    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']

    def __str__(self):
        return f'Платеж #{self.pk} по брони #{self.booking_id}'

    @property
    def status_label(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    @property
    def status_badge_class(self):
        return {
            self.STATUS_PENDING: 'payment-status-pending bg-warning text-dark',
            self.STATUS_SUCCESS: 'payment-status-success bg-success',
            self.STATUS_FAIL: 'payment-status-fail bg-danger',
        }.get(self.status, 'bg-secondary')
