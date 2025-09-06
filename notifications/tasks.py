from celery import shared_task
from groups.models import Group
from users.models import User
from .services import db_service, mail_service

GROUP_STATUS_MESSAGES = {
    "reached": {
        "title": "已達標",
        "content": "您參與的團購已成功達標，請等候團主通知後續事宜！",
    },
    "failed": {
        "title": "揪團失敗",
        "content": "由於未達目標，您參與的團購已結束。",
    },
    "deleted": {
        "title": "團購已取消",
        "content": "您參與的團購已被團主取消。",
    },
}


@shared_task
def trigger_notification_task(group_id, status):
    try:
        group = Group.objects.get(id=group_id)

        status_info = GROUP_STATUS_MESSAGES.get(status)
        if not status_info:
            return

        title = f"團購狀態更新：{status_info['title']} - {group.name}"
        content = status_info["content"]

        owner_id = group.owner_id
        all_participant_ids = list(
            group.joinedgroup_set.values_list("buyer_id", flat=True)
        )
        all_participant_ids.append(owner_id)

        # 建立站內通知
        db_service.create_notifications_for_event(
            all_participant_ids,
            group,
            title,
            content,
        )

        # 找出已驗證的使用者 Email
        verified_user_emails = list(
            User.objects.filter(
                id__in=all_participant_ids,
                is_verified=True,
            ).values_list("email", flat=True)
        )

        # 發送 Email 通知
        if verified_user_emails:
            mail_service.send_bulk_email_notifications(
                verified_user_emails,
                group,
                status_info["title"],
            )

    except Group.DoesNotExist:
        print(f"Task failed: Group with id={group_id} not found.")