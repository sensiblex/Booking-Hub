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
    except (OSError, SyntaxError, ValueError):
        return


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True, verbose_name="Название")
    slug = models.SlugField(max_length=140, unique=True, verbose_name="Слаг")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Amenity(models.Model):
    name = models.CharField(max_length=120, unique=True, verbose_name="Название")
    slug = models.SlugField(max_length=140, unique=True, verbose_name="Слаг")
    icon = models.CharField(max_length=60, blank=True, verbose_name="Bootstrap icon")

    class Meta:
        verbose_name = "Удобство"
        verbose_name_plural = "Удобства"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Space(models.Model):
    MODERATION_PENDING = "pending"
    MODERATION_APPROVED = "approved"
    MODERATION_REJECTED = "rejected"
    MODERATION_STATUS_CHOICES = (
        (MODERATION_PENDING, "На модерации"),
        (MODERATION_APPROVED, "Одобрено"),
        (MODERATION_REJECTED, "Отклонено"),
    )

    name = models.CharField(max_length=200, verbose_name="Название")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="spaces",
        verbose_name="Категория",
    )
    address = models.CharField(max_length=300, verbose_name="Адрес")
    capacity = models.PositiveIntegerField(verbose_name="Вместимость (чел.)")
    price_per_hour = models.PositiveIntegerField(verbose_name="Цена за час (₽)")

    description = models.TextField(blank=True, verbose_name="Описание")
    amenities = models.ManyToManyField(
        Amenity,
        blank=True,
        related_name="spaces",
        verbose_name="Удобства",
    )

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

    submitted_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="submitted_spaces",
        verbose_name="Кем добавлено",
    )
    moderation_status = models.CharField(
        max_length=20,
        choices=MODERATION_STATUS_CHOICES,
        default=MODERATION_APPROVED,
        db_index=True,
        verbose_name="Статус модерации",
    )
    moderation_note = models.TextField(blank=True, verbose_name="Комментарий модерации")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        _process_space_image(self.image)

    @property
    def display_amenities(self):
        amenities = list(self.amenities.all())
        if amenities:
            return amenities

        fallback = []
        if self.has_wifi:
            fallback.append({'name': 'Wi-Fi', 'icon': 'bi-wifi'})
        if self.has_projector:
            fallback.append({'name': 'Проектор', 'icon': 'bi-projector'})
        if self.has_board:
            fallback.append({'name': 'Маркерная доска', 'icon': 'bi-easel2'})
        return fallback

    class Meta:
        verbose_name = "Помещение"
        verbose_name_plural = "Помещения"


class SpacePhoto(models.Model):
    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name="photos",
        verbose_name="Помещение",
    )
    image = models.ImageField(
        upload_to='spaces/gallery/%Y/%m/',
        verbose_name="Фото",
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp'],
                message="Допустимые форматы: jpg, jpeg, png, webp"
            ),
            validate_space_image_size,
        ],
    )
    alt_text = models.CharField(max_length=200, blank=True, verbose_name="Описание фото")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Фото помещения"
        verbose_name_plural = "Фото помещений"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.alt_text or f"Фото: {self.space}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        _process_space_image(self.image)


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


@receiver(post_delete, sender=SpacePhoto)
def space_photo_post_delete(sender, instance, **kwargs):
    if instance.image:
        _delete_file(instance.image.path)


@receiver(pre_save, sender=SpacePhoto)
def space_photo_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = SpacePhoto.objects.get(pk=instance.pk)
    except SpacePhoto.DoesNotExist:
        return
    if old.image and old.image != instance.image:
        _delete_file(old.image.path)
