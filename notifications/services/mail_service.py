from django.urls import reverse
from anymail.message import AnymailMessage
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_group_notification_email(recipient_emails, group, status, is_bulk=False):
    """處理所有「團購狀態變更」相關的郵件"""
    try:
        group_url = f"{settings.SITE_URL}{reverse('groups:detail', kwargs={'id': group.id})}"
        template_mapping = (
            {"已成團": "跟團者達標通知信"} if is_bulk else {"已成團": "團主達標通知信"}
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
        order_url = f"{settings.SITE_URL}{order_list_path}?auto_tab={order.order_status}"
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