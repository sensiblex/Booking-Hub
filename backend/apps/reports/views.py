# apps/reports/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .services import ReportService


@login_required
def reports_dashboard(request):
    """Страница отчётов и аналитики"""
    return render(request, 'reports/dashboard.html')


@login_required
def reports_api(request):
    """API для получения данных отчётов"""
    period = int(request.GET.get('period', 30))
    
    # Используем сервис для агрегации данных
    service = ReportService(request.user, period_days=period)
    data = service.get_full_report()
    
    return JsonResponse(data)