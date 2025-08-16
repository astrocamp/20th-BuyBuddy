from .models import UserNotification


def navbar_notifications(request):
    if not request.user.is_authenticated:
        return {}

    qs = (
        UserNotification.objects.filter(user=request.user)
        .select_related("notification")
        .order_by("-notification__created_at")
    )

    notifications = qs[:5]
    unread_count = qs.filter(is_read=False).count()

    return {"notifications": notifications, "unread_count": unread_count}
