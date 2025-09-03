from django.shortcuts import get_object_or_404
from users.models import User
from .db_service import create_notification, create_bulk_notifications
from .mail_service import send_email_notification, send_bulk_email_notifications

GROUP_STATUS = {"reached": "已成團", "failed": "揪團失敗"}


def send_notification(user_id, group):
    group_status = GROUP_STATUS.get(group.status, "狀態更新")

    create_notification(user_id, group, group_status)

    user = get_object_or_404(User, pk=user_id)

    if user.is_verified:
        send_email_notification(user.email, group, group_status)


def send_bulk_notifications(user_ids, group):
    group_status = GROUP_STATUS.get(group.status, "狀態更新")

    create_bulk_notifications(user_ids, group, group_status)

    verified_user_emails = User.objects.filter(
        id__in=user_ids, is_verified=True
    ).values_list("email", flat=True)

    if verified_user_emails:
        send_bulk_email_notifications(list(verified_user_emails), group, group_status)
