from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from apps.users.views_admin import admin_dashboard

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # Админ-панель (только для staff/administrator)
    path('admin-panel/', admin_dashboard, name='admin_dashboard'),

    # Подключаем urls пользователей
    path('users/', include('apps.users.urls')),

    # Подключаем urls пространств
    path('spaces/', include('apps.spaces.urls')),

    # Главная страница — редирект на логин
    path('', RedirectView.as_view(url='/users/login/', permanent=False), name='home'),

    # favicon (чтобы не было 404 ошибки)
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
]
