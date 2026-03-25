from django.urls import path
from .views import register, login_view, logout_view, profile
from django.views.generic import RedirectView

app_name = 'users'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile, name='profile'),
    # profile и другие URL добавит Максим позже
]
