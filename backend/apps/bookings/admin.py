from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'space',
        'check_in',
        'check_out',
        'guests',
        'status',
        'total_price',
        'created_at',
    )
    list_filter = ('status', 'space', 'created_at')
    search_fields = ('user__username', 'user__email', 'space__name')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'check_in'
    ordering = ('-check_in',)
