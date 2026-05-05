from django.urls import path

from .views import reports_dashboard, reports_api


# reports/urls.py
urlpatterns = [
    path('dashboard/', reports_dashboard, name='reports_dashboard'),
    path('', reports_dashboard, name='reports_dashboard_short'),  # Редирект с /reports/ на /reports/dashboard/
    path('api/dashboard/', reports_api, name='reports_api'),  # API endpoint
]

