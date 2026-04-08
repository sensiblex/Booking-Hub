from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.role = 'client'
            user.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('/users/profile/')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_role_display()}!')
            return redirect('/users/profile/')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('/users/login/')


def profile(request):
    return render(request, 'auth/profile.html', {'user': request.user})


@login_required
def admin_users(request):
    if request.user.role != 'administrator' and not request.user.is_superuser:
        messages.error(request, 'Доступ запрещён.')
        return redirect('users:profile')

    qs = User.objects.all().order_by('-date_joined')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            __import__('django.db.models', fromlist=['Q']).Q(username__icontains=q) |
            __import__('django.db.models', fromlist=['Q']).Q(email__icontains=q) |
            __import__('django.db.models', fromlist=['Q']).Q(first_name__icontains=q) |
            __import__('django.db.models', fromlist=['Q']).Q(last_name__icontains=q)
        )

    role = request.GET.get('role', '')
    if role:
        qs = qs.filter(role=role)

    is_active = request.GET.get('is_active', '')
    if is_active == '1':
        qs = qs.filter(is_active=True)
    elif is_active == '0':
        qs = qs.filter(is_active=False)

    return render(request, 'admin/users.html', {
        'users': qs,
        'role_choices': User.ROLE_CHOICES,
    })


@login_required
def admin_change_role(request, user_id):
    if request.user.role != 'administrator' and not request.user.is_superuser:
        messages.error(request, 'Доступ запрещён.')
        return redirect('users:profile')
    if request.method == 'POST':
        u = get_object_or_404(User, pk=user_id)
        new_role = request.POST.get('role')
        valid_roles = [r[0] for r in User.ROLE_CHOICES]
        if new_role in valid_roles:
            u.role = new_role
            u.save()
            messages.success(request, f'Роль пользователя {u.username} изменена.')
    return redirect('users:admin_users')


@login_required
def admin_toggle_active(request, user_id):
    if request.user.role != 'administrator' and not request.user.is_superuser:
        messages.error(request, 'Доступ запрещён.')
        return redirect('users:profile')
    if request.method == 'POST':
        u = get_object_or_404(User, pk=user_id)
        if u == request.user:
            messages.warning(request, 'Нельзя заблокировать самого себя.')
        else:
            u.is_active = not u.is_active
            u.save()
            action = 'разблокирован' if u.is_active else 'заблокирован'
            messages.success(request, f'Пользователь {u.username} {action}.')
    return redirect('users:admin_users')
