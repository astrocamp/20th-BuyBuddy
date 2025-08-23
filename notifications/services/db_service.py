from ..models import UserNotification, Notification


def create_notification(user_id, group, group_status):
    title = f"{group_status} {group.name}"

    new_notification = Notification.objects.create(
        title=title, content="您開的團更新了，快去看看！", group=group
    )

    UserNotification.objects.create(
        user_id=user_id,
        notification=new_notification,
    )
    return 1


def create_bulk_notifications(user_ids, group, group_status):
    title = f"{group_status} {group.name}"

    new_notification = Notification.objects.create(
        title=title,
        content="您跟的團更新了，快去看看！",
        group=group,
    )

    unique_user_ids = set(user_ids)
    links = []
    for uid in unique_user_ids:
        links.append(
            UserNotification(
                user_id=uid,
                notification=new_notification,
            )
        )
    UserNotification.objects.bulk_create(links)
    return len(unique_user_ids)
