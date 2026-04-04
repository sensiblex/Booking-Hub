from django.contrib import admin
from django.utils.html import format_html
from .models import Space


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'address',
        'capacity',
        'price_per_hour',
        'has_projector',
        'has_board',
        'has_wifi',
        'preview_image',
        'created_at',
    )

    list_filter = (
        'has_projector',
        'has_board',
        'has_wifi',
    )

    search_fields = ('name', 'address', 'description')

    list_editable = (
        'has_projector',
        'has_board',
        'has_wifi',
    )

    readonly_fields = ('created_at', 'preview_image')

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'address', 'description')
        }),
        ('Параметры', {
            'fields': ('capacity', 'price_per_hour')
        }),
        ('Удобства', {
            'fields': ('has_projector', 'has_board', 'has_wifi')
        }),
        ('Медиа', {
            'fields': ('image', 'preview_image')
        }),
        ('Служебное', {
            'fields': ('created_at',)
        }),
    )

    ordering = ('-created_at',)
    list_per_page = 20

    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px; border-radius:4px;" />', obj.image.url)
        return '—'
    preview_image.short_description = 'Превью'
