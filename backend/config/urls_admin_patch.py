# Добавь этот URL в главный urls.py проекта:
#
#   from apps.users.views_admin import admin_dashboard
#   path('admin-panel/', admin_dashboard, name='admin_dashboard'),
#
# Пример итогового urls.py:
#
# from django.contrib import admin
# from django.urls import path, include
# from apps.users.views_admin import admin_dashboard
#
# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('admin-panel/', admin_dashboard, name='admin_dashboard'),
#     path('users/', include('apps.users.urls', namespace='users')),
#     path('spaces/', include('apps.spaces.urls', namespace='spaces')),
#     path('bookings/', include('apps.bookings.urls', namespace='bookings')),
# ]
