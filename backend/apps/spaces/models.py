from django.db import models

class Space(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    address = models.CharField(max_length=300, verbose_name="Адрес")
    capacity = models.PositiveIntegerField(verbose_name="Вместимость (чел.)")
    price_per_hour = models.PositiveIntegerField(verbose_name="Цена за час (₽)")
    
    description = models.TextField(blank=True, verbose_name="Описание")
    
    has_projector = models.BooleanField(default=False, verbose_name="Есть проектор")
    has_board = models.BooleanField(default=False, verbose_name="Есть доска")
    has_wifi = models.BooleanField(default=True, verbose_name="Есть Wi-Fi")
    
    image = models.ImageField(upload_to='spaces/', blank=True, null=True, verbose_name="Фото")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Помещение"
        verbose_name_plural = "Помещения"   