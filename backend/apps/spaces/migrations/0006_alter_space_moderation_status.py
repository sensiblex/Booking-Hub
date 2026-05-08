from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spaces', '0005_space_moderation_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='space',
            name='moderation_status',
            field=models.CharField(
                choices=[
                    ('pending', 'На модерации'),
                    ('approved', 'Одобрено'),
                    ('rejected', 'Отклонено'),
                    ('revision_required', 'На доработку'),
                ],
                db_index=True,
                default='approved',
                max_length=20,
                verbose_name='Статус модерации',
            ),
        ),
    ]
