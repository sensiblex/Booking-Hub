from django.urls import path

from .views import payment_fail, payment_pay, payment_success


app_name = 'payments'

urlpatterns = [
    path('pay/', payment_pay, name='pay'),
    path('pay/<int:booking_id>/', payment_pay, name='pay_for_booking'),
    path('success/', payment_success, name='success'),
    path('fail/', payment_fail, name='fail'),
]
