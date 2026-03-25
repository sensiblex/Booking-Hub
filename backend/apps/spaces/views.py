from django.shortcuts import render, get_object_or_404
from .models import Space

def space_list(request):
    spaces = Space.objects.all()
    return render(request, 'spaces/list.html', {'spaces': spaces})


def space_detail(request, pk):
    space = get_object_or_404(Space, pk=pk)
    return render(request, 'spaces/detail.html', {'space': space})