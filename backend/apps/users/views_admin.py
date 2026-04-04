from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

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
        'users_count': CustomUser.objects.count() if CustomUser else None,
        'spaces_count': Space.objects.count() if Space else None,
        'bookings_count': Booking.objects.count() if Booking else None,
        'payments_count': Payment.objects.count() if Payment else None,
    }
    return render(request, 'admin/dashboard.html', context)
