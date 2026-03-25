# backend/config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Добавьте другие маршруты по мере необходимости
    # path('api/', include('apps.api.urls')),
    # path('', include('apps.core.urls')),
]