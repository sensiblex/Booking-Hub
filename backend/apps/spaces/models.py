from django.db import models
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
                # Конвертируем RGBA/P в RGB для JPEG
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                # Уменьшаем до 1600x1600 сохраняя пропорции
                img.thumbnail((1600, 1600), Image.LANCZOS)
                # Сохраняем со сжатием quality=85
                img.save(self.image.path, format='JPEG', quality=85, optimize=True)
            except Exception:
                pass  # если файл недоступен, не падаем

    class Meta:
        verbose_name = "Помещение"
        verbose_name_plural = "Помещения"
