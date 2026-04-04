from django.urls import path
from . import views

app_name = 'spaces'

urlpatterns = [
    path('', views.space_list, name='list'),
    path('<int:pk>/', views.space_detail, name='detail'),
    # Добавьте другие URL по необходимости
]
