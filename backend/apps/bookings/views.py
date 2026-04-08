from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.spaces.models import Space


#====================================================================================
#                       Затычки (Пусть Амирчик бэк доделывает)
#====================================================================================
def booking_create(request, space_id):
    space = get_object_or_404(Space, id=space_id)
    
    if request.method == 'POST':
        messages.success(request, "Бронирование успешно создано! (тестовый режим)")
        return redirect('bookings:history')
    
    return render(request, 'bookings/create.html', {'space': space})


def booking_history(request):
    # Пока показываем пустой список или тестовые данные
    bookings = []  # можно позже заменить на реальные
    return render(request, 'bookings/history.html', {'bookings': bookings})


def manager_bookings(request):
    # Проверка доступа временно отключена
    bookings = []  
    return render(request, 'manager/bookings.html', {'bookings': bookings})


def cancel_booking(request, booking_id):
    messages.info(request, f"Бронирование #{booking_id} отменено (тестовый режим)")
    return redirect('bookings:history')