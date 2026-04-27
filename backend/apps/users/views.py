from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class AdminUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'is_active',
            'is_staff',
            'password1',
            'password2',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'adm-input', 'placeholder': 'username'}),
            'email': forms.EmailInput(attrs={'class': 'adm-input', 'placeholder': 'user@example.com'}),
            'first_name': forms.TextInput(attrs={'class': 'adm-input', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'adm-input', 'placeholder': 'Фамилия'}),
            'role': forms.Select(attrs={'class': 'adm-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'adm-input',
            'placeholder': 'Пароль',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'adm-input',
            'placeholder': 'Повторите пароль',
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        if user.role == 'administrator':
            user.is_staff = True
        if commit:
            user.save()
        return user


class UsernameOrEmailAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            auth_username = username
            if '@' in username:
                user = User.objects.filter(email__iexact=username).order_by('id').first()
                if user is not None:
                    auth_username = user.get_username()

            self.user_cache = authenticate(
                self.request,
                username=auth_username,
                password=password,
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


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
    if request.user.is_authenticated:
        return redirect('/users/profile/')

    next_url = request.GET.get('next') or request.POST.get('next') or '/users/profile/'

    if request.method == 'POST':
        form = UsernameOrEmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_role_display()}!')
            return redirect(next_url)
        messages.error(request, 'Не удалось войти. Проверьте имя пользователя и пароль.')
    else:
        form = UsernameOrEmailAuthenticationForm()
    return render(request, 'auth/login.html', {
        'form': form,
        'next': next_url,
    })


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('/users/login/')


@login_required(login_url='/users/login/')
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
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
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
def admin_user_create(request):
    if request.user.role != 'administrator' and not request.user.is_superuser:
        messages.error(request, 'Доступ запрещён.')
        return redirect('users:profile')

    form = AdminUserCreationForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Пользователь {user.username} создан.')
            return redirect('users:admin_users')
        messages.error(request, 'Проверьте данные формы.')

    return render(request, 'admin/user_form.html', {
        'form': form,
        'action': 'Добавить пользователя',
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
            if new_role == 'administrator':
                u.is_staff = True
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
