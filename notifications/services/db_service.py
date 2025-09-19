import logging
from ..models import UserNotification, Notification

logger = logging.getLogger(__name__)


def create_notification_for_event(group, user_ids, title, content):
    print(f"DEBUG: create_notification_for_event called for group {group.name}, users {user_ids}")
    if not user_ids:
        return 0
    try:
        new_notification = Notification.objects.create(
            title=title,
            content=content,
            group=group,
        )
        unique_user_ids = set(user_ids)
        user_notification_links = [
            UserNotification(user_id=uid, notification=new_notification)
            for uid in unique_user_ids
        ]
        UserNotification.objects.bulk_create(user_notification_links)
        logger.info(
            f"成功為 {len(unique_user_ids)} 個用戶創建了與團購 '{group.name}' 相關的站內通知。"
        )
        print(f"DEBUG: create_notification_for_event finished. Created {len(unique_user_ids)} notifications.")
        return len(unique_user_ids)
    except Exception as e:
        logger.error(
            f"創建事件通知時失敗 (Group ID: {group.id}): {e}", exc_info=True)
        return 0