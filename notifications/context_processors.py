from .models import UserNotification


def navbar_notifications(request):
    if not request.user.is_authenticated:
        return {}

    all_user_notifications = (
        UserNotification.objects.filter(user=request.user)
        .select_related("notification")
        .order_by("-notification__created_at")
    )

    unread_count = all_user_notifications.filter(is_read=False).count()

    return {"notifications": all_user_notifications, "unread_count": unread_count}
