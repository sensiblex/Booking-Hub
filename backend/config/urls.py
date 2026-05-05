from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from apps.users.views_admin import (
    admin_dashboard,
    admin_dashboard_api,
    admin_spaces, admin_space_create, admin_space_edit, admin_space_delete,
    admin_bookings, admin_booking_status,
    admin_payments,
)

urlpatterns = [
    path('django-admin/', admin.site.urls),

    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # Custom Admin Panel
    path('admin-panel/',                                  admin_dashboard,      name='admin_dashboard'),
    path('admin-panel/api/dashboard/',                    admin_dashboard_api,  name='admin_dashboard_api'),
    path('admin-panel/spaces/',                           admin_spaces,         name='admin_spaces'),
    path('admin-panel/spaces/add/',                       admin_space_create,   name='admin_space_create'),
    path('admin-panel/spaces/<int:space_id>/edit/',       admin_space_edit,     name='admin_space_edit'),
    path('admin-panel/spaces/<int:space_id>/delete/',     admin_space_delete,   name='admin_space_delete'),
    path('admin-panel/bookings/',                         admin_bookings,       name='admin_bookings'),
    path('admin-panel/bookings/<int:booking_id>/status/', admin_booking_status, name='admin_booking_status'),
    path('admin-panel/payments/',                         admin_payments,       name='admin_payments'),
    

    
    #Бронирование
    path('bookings/', include('apps.bookings.urls')),
    path('payments/', include('apps.payments.urls')),
    
    # Apps
    path('users/',  include('apps.users.urls')),
    path('spaces/', include('apps.spaces.urls')),

    # Отчеты
    path('reports/', include('apps.reports.urls')),
]

# СТАЛО
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
