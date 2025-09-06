from ..models import UserNotification, Notification


def create_notifications_for_event(user_ids, group, title, content):
    # 建立一筆共用的 Notification
    notification_obj = Notification.objects.create(
        title=title,
        content=content,
        group=group,
    )

    # 為所有使用者建立關聯
    unique_user_ids = set(user_ids)
    links = [
        UserNotification(user_id=uid, notification=notification_obj)
        for uid in unique_user_ids
    ]

    if links:
        UserNotification.objects.bulk_create(links)

    return len(unique_user_ids)