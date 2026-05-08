from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('space_submitted', 'Помещение отправлено на модерацию'), ('space_resubmitted', 'Помещение отправлено повторно'), ('space_approved', 'Помещение одобрено'), ('space_rejected', 'Помещение отклонено'), ('space_revision_required', 'Помещение отправлено на доработку'), ('booking_request', 'Новая заявка на аренду'), ('booking_approved', 'Аренда одобрена'), ('booking_declined', 'Аренда отклонена')], max_length=40, verbose_name='Тип')),
                ('title', models.CharField(max_length=160, verbose_name='Заголовок')),
                ('message', models.TextField(verbose_name='Сообщение')),
                ('url', models.CharField(blank=True, max_length=400, verbose_name='Ссылка')),
                ('is_read', models.BooleanField(db_index=True, default=False, verbose_name='Прочитано')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Создано')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Уведомление',
                'verbose_name_plural': 'Уведомления',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', '-created_at'], name='notificatio_user_id_50e6e5_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', 'is_read'], name='notificatio_user_id_2acf15_idx'),
        ),
    ]
