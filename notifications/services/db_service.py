from ..models import UserNotification, Notification

GROUP_STATUS = {"reached": "已成團", "failed": "揪團失敗"}


def notify_owner(user_id, group):
    if not group:
        return 0

    group_status = GROUP_STATUS[group.status]
    title = f"{group_status} {group.name}"

    new_notification = Notification.objects.create(
        title=title, content="您開的團更新了，快去看看！", group=group
    )

    UserNotification.objects.create(
        user_id=user_id,
        notification=new_notification,
    )
    return 1


def notify_buyer(user_ids, group):
    if not group:
        return 0

    group_status = GROUP_STATUS[group.status]
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
