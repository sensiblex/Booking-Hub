from .models import Notification


def notifications_context(request):
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {
            'nav_notifications': [],
            'unread_notifications_count': 0,
            'toast_notifications': [],
        }

    nav_notifications = list(
        Notification.objects.filter(user=request.user)
        .order_by('-created_at')[:8]
    )
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    toast_notifications = []
    fresh_ids = request.session.pop('fresh_notification_ids', [])
    if fresh_ids:
        toast_notifications = list(
            Notification.objects.filter(user=request.user, id__in=fresh_ids).order_by('created_at')
        )

    return {
        'nav_notifications': nav_notifications,
        'unread_notifications_count': unread_count,
        'toast_notifications': toast_notifications,
    }
