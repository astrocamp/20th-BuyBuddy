import logging
from anymail.message import AnymailMessage

from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


def send_group_notification_email(recipient_emails, group, status, is_bulk=False):
    """處理所有「團購狀態變更」相關的郵件"""
    try:
        group_url = (
            f"{settings.SITE_URL}{reverse('groups:detail', kwargs={'id': group.id})}"
        )
        template_mapping = (
            {"已達標": "跟團者達標通知信"} if is_bulk else {"已達標": "團主達標通知信"}
        )
        template_id = template_mapping.get(
            status,
            "跟團者通用通知信" if is_bulk else "團主通用通知信",
        )

        mail = AnymailMessage(template_id=template_id, to=recipient_emails)
        mail.merge_global_data = {
            "group_url": group_url,
            "homepage_url": settings.SITE_URL,
            "group_name": group.name,
            "group_status": status,
        }
        mail.send()

    except Exception as e:
        logger.error(f"發送團購狀態郵件失敗: {e}", exc_info=True)
        raise


def send_order_notification_email(recipient_emails, order, status, is_bulk=False):
    """處理所有「訂單狀態變更」相關的郵件"""
    try:
        order_list_path = reverse("orders:my_orders")
        order_url = (
            f"{settings.SITE_URL}{order_list_path}?auto_tab={order.order_status}"
        )
        group = order.group

        if is_bulk:
            template_mapping = {
                "訂單「待出貨」": "跟團者訂單待出貨通知信",
                "訂單「已付款」": "跟團者訂單已付款通知信",
                "訂單「已出貨」": "跟團者訂單已出貨通知信",
                "訂單「已完成」": "跟團者訂單已完成通知信",
            }
            template_id = template_mapping.get(status, "跟團者通用通知信")
        else:
            template_mapping = {
                "團購收到新訂單": "團主新訂單通知信",
                "訂單「待出貨」": "團主訂單待出貨通知信",
                "訂單「已付款」": "團主訂單已付款通知信",
                "訂單「已出貨」": "團主訂單已出貨通知信",
                "訂單「已完成」": "團主訂單已完成通知信",
            }
            template_id = template_mapping.get(status, "團主通用通知信")

        mail = AnymailMessage(template_id=template_id, to=recipient_emails)
        mail.merge_global_data = {
            "order_url": order_url,
            "homepage_url": settings.SITE_URL,
            "group_name": group.name,
            "group_status": status,
            "buyer_name": order.user.username,
        }
        mail.send()

    except Exception as e:
        logger.error(f"發送訂單狀態郵件失敗: {e}", exc_info=True)
        raise


def send_new_message_email(
    recipient_email,
    sender_username,
    order_number,
    message_content,
    order_id,
    receiver_is_owner,
):
    """Sends an email notification for a new order message."""
    try:
        subject = f"訂單 #{order_number} 有新留言：來自 {sender_username}"
        template_id = "訂單新留言通知信"

        if receiver_is_owner:
            message_board_url = f"{settings.SITE_URL}{reverse('orders:group_owner_order_messages', kwargs={'order_id': order_id})}"
        else:
            message_board_url = f"{settings.SITE_URL}{reverse('orders:order_messages', kwargs={'order_id': order_id})}"

        mail = AnymailMessage(template_id=template_id, to=[recipient_email])
        mail.merge_global_data = {
            "order_number": order_number,
            "sender_username": sender_username,
            "message_content": message_content,
            "homepage_url": settings.SITE_URL,
            "message_board_url": message_board_url,
        }
        mail.send()
        logger.info(
            f"📧 已將訂單 #{order_number} 的新留言郵件發送給 {recipient_email}。"
        )
    except Exception as e:
        logger.error(f"發送訂單新留言郵件失敗: {e}", exc_info=True)
        raise
