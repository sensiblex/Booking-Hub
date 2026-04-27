from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
        'is_active',
        'is_staff',
        'date_joined',
    )
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_editable = ('role', 'is_active')
    readonly_fields = ('last_login', 'date_joined')
    list_per_page = 25
    actions = (
        'make_clients',
        'make_managers',
        'make_administrators',
        'activate_users',
        'deactivate_users',
    )

    fieldsets = UserAdmin.fieldsets + (
        ('Роль и права', {
            'fields': ('role',)
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Роль и права', {
            'fields': ('role',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if obj.role == 'administrator':
            obj.is_staff = True
        super().save_model(request, obj, form, change)

    @admin.action(description='Назначить роль "Клиент"')
    def make_clients(self, request, queryset):
        queryset.update(role='client')

    @admin.action(description='Назначить роль "Менеджер"')
    def make_managers(self, request, queryset):
        queryset.update(role='manager')

    @admin.action(description='Назначить роль "Администратор"')
    def make_administrators(self, request, queryset):
        queryset.update(role='administrator', is_staff=True)

    @admin.action(description='Активировать выбранных пользователей')
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Заблокировать выбранных пользователей')
    def deactivate_users(self, request, queryset):
        queryset.exclude(pk=request.user.pk).update(is_active=False)
