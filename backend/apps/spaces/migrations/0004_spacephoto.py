import django.core.validators
from django.db import migrations, models
import django.db.models.deletion

import apps.spaces.models


class Migration(migrations.Migration):

    dependencies = [
        ('spaces', '0003_category_amenity_space_catalog_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpacePhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='spaces/gallery/%Y/%m/', validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=['jpg', 'jpeg', 'png', 'webp'],
                        message='Допустимые форматы: jpg, jpeg, png, webp',
                    ),
                    apps.spaces.models.validate_space_image_size,
                ], verbose_name='Фото')),
                ('alt_text', models.CharField(blank=True, max_length=200, verbose_name='Описание фото')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('space', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='spaces.space', verbose_name='Помещение')),
            ],
            options={
                'verbose_name': 'Фото помещения',
                'verbose_name_plural': 'Фото помещений',
                'ordering': ['sort_order', 'id'],
            },
        ),
    ]
