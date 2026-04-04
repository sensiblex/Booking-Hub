import os
from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.core.validators import FileExtensionValidator
from PIL import Image


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
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'webp'],
            message="Допустимые форматы: jpg, jpeg, png, webp"
        )]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            try:
                img = Image.open(self.image.path)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                img.thumbnail((1600, 1600), Image.LANCZOS)
                img.save(self.image.path, format='JPEG', quality=85, optimize=True)
            except Exception:
                pass

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
