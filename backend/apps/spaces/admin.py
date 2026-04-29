from django.contrib import admin
from django.utils.html import format_html
from .models import Amenity, Category, Space, SpacePhoto


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class SpacePhotoInline(admin.TabularInline):
    model = SpacePhoto
    extra = 1
    fields = ('preview_image', 'image', 'alt_text', 'sort_order')
    readonly_fields = ('preview_image',)

    @admin.display(description='Превью')
    def preview_image(self, obj):
        if obj.image and obj.image.name:
            return format_html(
                '<img src="{}" style="width:72px;height:48px;object-fit:cover;border-radius:4px;" />',
                obj.image.url,
            )
        return '—'


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = (
        'preview_image',
        'name',
        'category',
        'address',
        'capacity',
        'price_per_hour',
        'has_projector',
        'has_board',
        'has_wifi',
        'created_at',
    )

    list_filter = (
        'category',
        'amenities',
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
            'fields': ('name', 'category', 'address', 'description')
        }),
        ('Параметры', {
            'fields': ('capacity', 'price_per_hour')
        }),
        ('Удобства', {
            'fields': ('amenities', 'has_projector', 'has_board', 'has_wifi')
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
    inlines = (SpacePhotoInline,)
    actions = (
        'enable_wifi',
        'enable_projector',
        'enable_board',
        'disable_projector',
        'disable_board',
    )

    @admin.display(description='Превью')
    def preview_image(self, obj):
        if obj.image and obj.image.name:
            return format_html(
                '<img src="{}" style="width:72px;height:48px;object-fit:cover;border-radius:4px;" />',
                obj.image.url,
            )
        return '—'

    @admin.action(description='Включить Wi-Fi')
    def enable_wifi(self, request, queryset):
        queryset.update(has_wifi=True)

    @admin.action(description='Добавить проектор')
    def enable_projector(self, request, queryset):
        queryset.update(has_projector=True)

    @admin.action(description='Добавить доску')
    def enable_board(self, request, queryset):
        queryset.update(has_board=True)

    @admin.action(description='Убрать проектор')
    def disable_projector(self, request, queryset):
        queryset.update(has_projector=False)

    @admin.action(description='Убрать доску')
    def disable_board(self, request, queryset):
        queryset.update(has_board=False)
