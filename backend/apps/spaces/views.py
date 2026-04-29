from django.shortcuts import render, get_object_or_404
from .models import Amenity, Category, Space
from .utils import filter_spaces

def space_list(request):
    spaces = filter_spaces(
        Space.objects.select_related('category').prefetch_related('amenities', 'photos'),
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
        Space.objects.select_related('category').prefetch_related('amenities', 'photos'),
        pk=pk,
    )
    return render(request, 'spaces/detail.html', {'space': space})
