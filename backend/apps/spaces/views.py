from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from apps.bookings.models import Booking
from .models import Amenity, Category, Space
from .forms import UserSpaceSubmissionForm
from .utils import filter_spaces

def space_list(request):
    spaces = filter_spaces(
        Space.objects.filter(moderation_status=Space.MODERATION_APPROVED)
        .select_related('category')
        .prefetch_related('amenities', 'photos'),
        request.GET,
    )
    return render(request, 'spaces/list.html', {
        'spaces': spaces,
        'categories': Category.objects.all(),
        'amenities': Amenity.objects.all(),
        'selected_amenities': request.GET.getlist('amenities'),
    })


def space_detail(request, pk):
    space = get_object_or_404(
        Space.objects.filter(moderation_status=Space.MODERATION_APPROVED)
        .select_related('category')
        .prefetch_related('amenities', 'photos'),
        pk=pk,
    )
    return render(request, 'spaces/detail.html', {'space': space})


@login_required(login_url='/users/login/')
def space_submit(request):
    form = UserSpaceSubmissionForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            space = form.save(commit=False)
            space.submitted_by = request.user
            space.moderation_status = Space.MODERATION_PENDING
            space.save()
            form.save_m2m()
            selected_amenities = set(space.amenities.values_list('slug', flat=True))
            if 'wifi' in selected_amenities:
                space.has_wifi = True
            if 'projector' in selected_amenities:
                space.has_projector = True
            if 'board' in selected_amenities:
                space.has_board = True
            space.save(update_fields=['has_wifi', 'has_projector', 'has_board'])
            messages.success(request, 'Помещение отправлено на модерацию.')
            return redirect('users:profile')
        messages.error(request, 'Проверьте данные формы.')
    return render(request, 'spaces/submit.html', {'form': form})


@login_required(login_url='/users/login/')
def my_spaces(request):
    spaces = request.user.submitted_spaces.all().select_related('category').prefetch_related(
        'bookings__user', 'amenities', 'photos'
    )
    for space in spaces:
        space.pending_bookings = space.bookings.filter(
            status=Booking.STATUS_AWAITING_CONFIRMATION
        ).select_related('user')
        space.other_bookings = space.bookings.exclude(
            status=Booking.STATUS_AWAITING_CONFIRMATION
        ).select_related('user')
    return render(request, 'spaces/my_spaces.html', {'spaces': spaces})


@login_required(login_url='/users/login/')
def confirm_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if booking.space.submitted_by != request.user:
        messages.error(request, 'Вы не можете управлять этим бронированием.')
        return redirect('spaces:my_spaces')
    if booking.status == Booking.STATUS_AWAITING_CONFIRMATION:
        booking.status = Booking.STATUS_CONFIRMED
        booking.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Бронирование #{booking.id} подтверждено.')
    return redirect('spaces:my_spaces')


@login_required(login_url='/users/login/')
def decline_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if booking.space.submitted_by != request.user:
        messages.error(request, 'Вы не можете управлять этим бронированием.')
        return redirect('spaces:my_spaces')
    if booking.status == Booking.STATUS_AWAITING_CONFIRMATION:
        booking.status = Booking.STATUS_CANCELLED
        booking.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Бронирование #{booking.id} отклонено.')
    return redirect('spaces:my_spaces')


@login_required(login_url='/users/login/')
def space_edit(request, pk):
    space = get_object_or_404(Space, pk=pk, submitted_by=request.user)
    if space.moderation_status == Space.MODERATION_APPROVED:
        messages.error(request, 'Нельзя редактировать опубликованное помещение.')
        return redirect('spaces:my_spaces')
    form = UserSpaceSubmissionForm(request.POST or None, request.FILES or None, instance=space)
    if request.method == 'POST':
        if form.is_valid():
            space = form.save(commit=False)
            space.moderation_status = Space.MODERATION_PENDING
            space.moderation_note = ''
            space.save()
            form.save_m2m()
            selected_amenities = set(space.amenities.values_list('slug', flat=True))
            if 'wifi' in selected_amenities:
                space.has_wifi = True
            if 'projector' in selected_amenities:
                space.has_projector = True
            if 'board' in selected_amenities:
                space.has_board = True
            space.save(update_fields=['has_wifi', 'has_projector', 'has_board'])
            messages.success(request, 'Помещение отправлено на модерацию.')
            return redirect('spaces:my_spaces')
        messages.error(request, 'Проверьте данные формы.')
    return render(request, 'spaces/edit.html', {'form': form, 'space': space})
