from django.urls import path
from . import views

app_name = 'spaces'

urlpatterns = [
    path('', views.space_list, name='list'),
    path('my/', views.my_spaces, name='my_spaces'),
    path('submit/', views.space_submit, name='submit'),
    path('<int:pk>/', views.space_detail, name='detail'),
    path('booking/<int:booking_id>/confirm/', views.confirm_booking, name='confirm_booking'),
    path('booking/<int:booking_id>/decline/', views.decline_booking, name='decline_booking'),
]
