import django.core.validators
from django.db import migrations, models

import apps.spaces.models


class Migration(migrations.Migration):

    dependencies = [
        ('spaces', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='space',
            name='image',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='spaces/%Y/%m/',
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=['jpg', 'jpeg', 'png', 'webp'],
                        message='Допустимые форматы: jpg, jpeg, png, webp',
                    ),
                    apps.spaces.models.validate_space_image_size,
                ],
                verbose_name='Фото',
            ),
        ),
    ]
