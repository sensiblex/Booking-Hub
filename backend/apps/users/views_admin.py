from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q

try:
    from apps.users.models import CustomUser
except ImportError:
    CustomUser = None

try:
    from apps.spaces.models import Space
except ImportError:
    Space = None

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
    context = {
        'users_count':    CustomUser.objects.count() if CustomUser else 0,
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
    if request.method == 'POST':
        try:
            Space.objects.create(
                name=request.POST['name'],
                address=request.POST['address'],
                capacity=int(request.POST['capacity']),
                price_per_hour=int(request.POST['price_per_hour']),
                description=request.POST.get('description', ''),
                has_projector='has_projector' in request.POST,
                has_board='has_board' in request.POST,
                has_wifi='has_wifi' in request.POST,
                image=request.FILES.get('image'),
            )
            messages.success(request, 'Помещение успешно добавлено.')
            return redirect('admin_spaces')
        except Exception as e:
            messages.error(request, f'Ошибка: {e}')
    return render(request, 'admin/space_form.html', {'action': 'Добавить', 'space': None})


@staff_member_required(login_url='/users/login/')
def admin_space_edit(request, space_id):
    space = get_object_or_404(Space, pk=space_id)
    if request.method == 'POST':
        try:
            space.name           = request.POST['name']
            space.address        = request.POST['address']
            space.capacity       = int(request.POST['capacity'])
            space.price_per_hour = int(request.POST['price_per_hour'])
            space.description    = request.POST.get('description', '')
            space.has_projector  = 'has_projector' in request.POST
            space.has_board      = 'has_board'      in request.POST
            space.has_wifi       = 'has_wifi'       in request.POST
            if request.FILES.get('image'):
                space.image = request.FILES['image']
            space.save()
            messages.success(request, 'Помещение обновлено.')
            return redirect('admin_spaces')
        except Exception as e:
            messages.error(request, f'Ошибка: {e}')
    return render(request, 'admin/space_form.html', {'action': 'Редактировать', 'space': space})


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
    if Booking is None:
        bookings = []
        status_choices = []
    else:
        status = request.GET.get('status', '').strip()
        q      = request.GET.get('q', '').strip()
        bookings = Booking.objects.select_related('user', 'space').order_by('-created_at') \
            if hasattr(Booking, 'objects') else []
        if status:
            bookings = bookings.filter(status=status)
        if q:
            bookings = bookings.filter(
                Q(user__username__icontains=q) | Q(space__name__icontains=q)
            )
        status_choices = Booking.STATUS_CHOICES if hasattr(Booking, 'STATUS_CHOICES') else []
    return render(request, 'admin/bookings.html', {
        'bookings': bookings,
        'status_choices': status_choices,
    })


@staff_member_required(login_url='/users/login/')
def admin_booking_status(request, booking_id):
    """Быстрое изменение статуса брони."""
    if Booking is None:
        return redirect('admin_bookings')
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            booking.status = new_status
            booking.save()
            messages.success(request, 'Статус обновлён.')
    return redirect('admin_bookings')


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
