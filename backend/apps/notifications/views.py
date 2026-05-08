from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification


@login_required(login_url='/users/login/')
def notification_list(request):
    only_unread = request.GET.get('filter') == 'unread'
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    if only_unread:
        notifications = notifications.filter(is_read=False)

    return render(request, 'notifications/list.html', {
        'notifications': notifications,
        'current_filter': 'unread' if only_unread else 'all',
    })


@login_required(login_url='/users/login/')
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    if request.method == 'POST':
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    next_url = request.POST.get('next') or request.GET.get('next') or 'notifications:list'
    return redirect(next_url)


@login_required(login_url='/users/login/')
def mark_all_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    next_url = request.POST.get('next') or request.GET.get('next') or 'notifications:list'
    return redirect(next_url)


@login_required(login_url='/users/login/')
def notification_updates_api(request):
    try:
        after_id = int(request.GET.get('after_id', '0'))
    except (TypeError, ValueError):
        after_id = 0

    updates_qs = (
        Notification.objects
        .filter(user=request.user, id__gt=after_id)
        .order_by('id')[:20]
    )
    updates = [
        {
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'url': n.url,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%d.%m.%Y %H:%M'),
        }
        for n in updates_qs
    ]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    latest_id = after_id
    if updates:
        latest_id = updates[-1]['id']

    return JsonResponse({
        'updates': updates,
        'unread_count': unread_count,
        'latest_id': latest_id,
    })
