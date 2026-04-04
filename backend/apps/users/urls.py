from django.urls import path
from .views import register, login_view, logout_view, profile, admin_users, admin_change_role, admin_toggle_active

app_name = 'users'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile, name='profile'),
    path('admin/users/', admin_users, name='admin_users'),
    path('admin/users/<int:user_id>/role/', admin_change_role, name='admin_change_role'),
    path('admin/users/<int:user_id>/toggle/', admin_toggle_active, name='admin_toggle_active'),
]
