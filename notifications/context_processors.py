from .models import UserNotification


def navbar_notifications(request):
    if not request.user.is_authenticated:
        return {}

    notifications_query = (
        UserNotification.objects.filter(user=request.user)
        .select_related("notification")
        .order_by("-notification__created_at")
    )

    unread_count = notifications_query.filter(is_read=False).count()
    all_user_notifications = notifications_query[:5]

    return {"notifications": all_user_notifications, "unread_count": unread_count}
