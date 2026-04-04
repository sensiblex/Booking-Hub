from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from django.conf import settings
from django.conf.urls.static import static
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
    path('', RedirectView.as_view(url='/users/login/', permanent=False), name='home_redirect'),

    # favicon
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
]

# Раздача медиафайлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
