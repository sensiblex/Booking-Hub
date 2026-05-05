from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

try:
    from apps.spaces.models import Space
    from apps.spaces.forms import SpaceForm
except ImportError:
    Space = None
    SpaceForm = None

try:
    from apps.bookings.models import Booking
except ImportError:
    Booking = None

try:
    from apps.payments.models import Payment
except ImportError:
    Payment = None


@staff_member_required(login_url='/users/login/')
def admin_dashboard(request):
    User = get_user_model()
    context = {
        'users_count':    User.objects.count(),
        'spaces_count':   Space.objects.count()      if Space      else 0,
        'bookings_count': Booking.objects.count()    if Booking    else 0,
        'payments_count': Payment.objects.count()    if Payment    else 0,
    }
    return render(request, 'admin/dashboard.html', context)


# ---- Spaces ----

@staff_member_required(login_url='/users/login/')
def admin_spaces(request):
    if Space is None:
        spaces = []
    else:
        q = request.GET.get('q', '').strip()
        spaces = Space.objects.all().order_by('-created_at')
        if q:
            spaces = spaces.filter(
                Q(name__icontains=q) | Q(address__icontains=q)
            )
    return render(request, 'admin/spaces.html', {'spaces': spaces})


@staff_member_required(login_url='/users/login/')
def admin_space_create(request):
    if SpaceForm is None:
        messages.error(request, 'Модуль помещений недоступен.')
        return redirect('admin_spaces')

    form = SpaceForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Помещение успешно добавлено.')
            return redirect('admin_spaces')
        messages.error(request, 'Проверьте данные формы.')
    return render(request, 'admin/space_form.html', {
        'action': 'Добавить',
        'form': form,
        'space': None,
    })


@staff_member_required(login_url='/users/login/')
def admin_space_edit(request, space_id):
    space = get_object_or_404(Space, pk=space_id)
    form = SpaceForm(request.POST or None, request.FILES or None, instance=space)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Помещение обновлено.')
            return redirect('admin_spaces')
        messages.error(request, 'Проверьте данные формы.')
    return render(request, 'admin/space_form.html', {
        'action': 'Редактировать',
        'form': form,
        'space': space,
    })


@staff_member_required(login_url='/users/login/')
def admin_space_delete(request, space_id):
    space = get_object_or_404(Space, pk=space_id)
    if request.method == 'POST':
        space.delete()
        messages.success(request, 'Помещение удалено.')
    return redirect('admin_spaces')


# ---- Bookings ----

@staff_member_required(login_url='/users/login/')
def admin_bookings(request):
    booking_stats = {
        'total': 0,
        'pending': 0,
        'confirmed': 0,
        'cancelled': 0,
    }

    if Booking is None:
        bookings = []
        status_choices = []
    else:
        status = request.GET.get('status', '').strip()
        q      = request.GET.get('q', '').strip()
        date_from = request.GET.get('date_from', '').strip()
        date_to = request.GET.get('date_to', '').strip()

        bookings = Booking.objects.select_related('user', 'space').order_by('-created_at') \
            if hasattr(Booking, 'objects') else []

        status_counts = Booking.objects.values('status').annotate(total=Count('id'))
        booking_stats.update({
            row['status']: row['total']
            for row in status_counts
        })
        booking_stats['total'] = Booking.objects.count()

        if status:
            bookings = bookings.filter(status=status)
        if q:
            bookings = bookings.filter(
                Q(user__username__icontains=q) |
                Q(user__email__icontains=q) |
                Q(space__name__icontains=q)
            )
        if date_from:
            bookings = bookings.filter(check_in__date__gte=date_from)
        if date_to:
            bookings = bookings.filter(check_in__date__lte=date_to)

        status_choices = Booking.STATUS_CHOICES if hasattr(Booking, 'STATUS_CHOICES') else []

    return render(request, 'admin/bookings.html', {
        'bookings': bookings,
        'status_choices': status_choices,
        'booking_stats': booking_stats,
    })


@staff_member_required(login_url='/users/login/')
def admin_booking_status(request, booking_id):
    """Быстрое изменение статуса брони."""
    if Booking is None:
        return redirect('admin_bookings')

    booking = get_object_or_404(Booking, pk=booking_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = [value for value, _label in Booking.STATUS_CHOICES]
        if new_status in valid_statuses:
            booking.status = new_status
            booking.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Статус обновлён.')
        else:
            messages.error(request, 'Некорректный статус бронирования.')

    next_url = request.POST.get('next') or reverse('admin_bookings')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = reverse('admin_bookings')
    return redirect(next_url)


# ---- Payments ----

@staff_member_required(login_url='/users/login/')
def admin_payments(request):
    if Payment is None:
        payments = []
        status_choices = []
    else:
        status = request.GET.get('status', '').strip()
        payments = Payment.objects.select_related('booking').order_by('-created_at') \
            if hasattr(Payment, 'objects') else []
        if status:
            payments = payments.filter(status=status)
        status_choices = Payment.STATUS_CHOICES if hasattr(Payment, 'STATUS_CHOICES') else []
    return render(request, 'admin/payments.html', {
        'payments': payments,
        'status_choices': status_choices,
    })
