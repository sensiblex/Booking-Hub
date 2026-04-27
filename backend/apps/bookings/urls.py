from django.urls import path
from .views import booking_create, booking_history, manager_bookings, cancel_booking

app_name = 'bookings'

urlpatterns = [
    path('create/<int:space_id>/', booking_create, name='create'),
    path('history/', booking_history, name='history'),
    path('manager/', manager_bookings, name='manager_bookings'),
    path('cancel/<int:booking_id>/', cancel_booking, name='cancel'),
    # profile и другие URL добавит Максим позже
]
