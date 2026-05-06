from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("spaces", "0004_spacephoto"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="space",
            name="moderation_note",
            field=models.TextField(blank=True, verbose_name="Комментарий модерации"),
        ),
        migrations.AddField(
            model_name="space",
            name="moderation_status",
            field=models.CharField(
                choices=[
                    ("pending", "На модерации"),
                    ("approved", "Одобрено"),
                    ("rejected", "Отклонено"),
                ],
                db_index=True,
                default="approved",
                max_length=20,
                verbose_name="Статус модерации",
            ),
        ),
        migrations.AddField(
            model_name="space",
            name="submitted_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="submitted_spaces",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Кем добавлено",
            ),
        ),
    ]
