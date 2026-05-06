from django.urls import path
from . import views

app_name = 'spaces'

urlpatterns = [
    path('', views.space_list, name='list'),
    path('submit/', views.space_submit, name='submit'),
    path('<int:pk>/', views.space_detail, name='detail'),
]
