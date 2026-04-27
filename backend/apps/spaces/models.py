import os
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.core.validators import FileExtensionValidator
from PIL import Image, ImageOps


MAX_SPACE_IMAGE_SIZE = 8 * 1024 * 1024


def validate_space_image_size(image):
    if image and image.size > MAX_SPACE_IMAGE_SIZE:
        raise ValidationError("Размер фото не должен превышать 8 МБ.")


def _process_space_image(image_field):
    if not image_field:
        return

    try:
        path = image_field.path
    except (NotImplementedError, ValueError):
        return

    if not path or not os.path.isfile(path):
        return

    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)
            resampling = getattr(Image, 'Resampling', Image).LANCZOS
            img.thumbnail((1600, 1600), resampling)

            extension = os.path.splitext(path)[1].lower()
            if extension in ('.jpg', '.jpeg'):
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(path, format='JPEG', quality=85, optimize=True)
            elif extension == '.png':
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGBA')
                img.save(path, format='PNG', optimize=True)
            elif extension == '.webp':
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                img.save(path, format='WEBP', quality=85, method=6)
    except (OSError, ValueError):
        return


class Space(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    address = models.CharField(max_length=300, verbose_name="Адрес")
    capacity = models.PositiveIntegerField(verbose_name="Вместимость (чел.)")
    price_per_hour = models.PositiveIntegerField(verbose_name="Цена за час (₽)")

    description = models.TextField(blank=True, verbose_name="Описание")

    has_projector = models.BooleanField(default=False, verbose_name="Есть проектор")
    has_board = models.BooleanField(default=False, verbose_name="Есть доска")
    has_wifi = models.BooleanField(default=True, verbose_name="Есть Wi-Fi")

    image = models.ImageField(
        upload_to='spaces/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Фото",
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp'],
                message="Допустимые форматы: jpg, jpeg, png, webp"
            ),
            validate_space_image_size,
        ]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        _process_space_image(self.image)

    class Meta:
        verbose_name = "Помещение"
        verbose_name_plural = "Помещения"


def _delete_file(path):
    """Удаляет файл с диска если он существует."""
    if path and os.path.isfile(path):
        os.remove(path)


@receiver(post_delete, sender=Space)
def space_post_delete(sender, instance, **kwargs):
    """При удалении помещения — удаляем файл изображения с диска."""
    if instance.image:
        _delete_file(instance.image.path)


@receiver(pre_save, sender=Space)
def space_pre_save(sender, instance, **kwargs):
    """При обновлении изображения — удаляем старый файл с диска."""
    if not instance.pk:
        return  # новый объект, нечего удалять
    try:
        old = Space.objects.get(pk=instance.pk)
    except Space.DoesNotExist:
        return
    if old.image and old.image != instance.image:
        _delete_file(old.image.path)
