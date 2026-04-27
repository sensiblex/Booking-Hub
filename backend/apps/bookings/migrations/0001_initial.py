# Generated manually for Booking-Hub booking backend.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('spaces', '0002_alter_space_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField(verbose_name='Начало бронирования')),
                ('end_time', models.DateTimeField(verbose_name='Окончание бронирования')),
                ('status', models.CharField(choices=[('pending', 'Ожидает'), ('confirmed', 'Подтверждено'), ('cancelled', 'Отменено')], default='pending', max_length=20, verbose_name='Статус')),
                ('total_price', models.PositiveIntegerField(default=0, verbose_name='Сумма')),
                ('comment', models.TextField(blank=True, verbose_name='Комментарий')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлено')),
                ('space', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='spaces.space', verbose_name='Помещение')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Бронирование',
                'verbose_name_plural': 'Бронирования',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['space', 'start_time', 'end_time'], name='bookings_bo_space_i_bbfde0_idx'),
                    models.Index(fields=['user', '-created_at'], name='bookings_bo_user_id_6151bb_idx'),
                    models.Index(fields=['status'], name='bookings_bo_status_233e96_idx'),
                ],
            },
        ),
    ]
