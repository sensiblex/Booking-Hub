from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
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
