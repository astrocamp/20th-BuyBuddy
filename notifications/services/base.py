import logging

from celery import shared_task

from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from groups.models import Group
from orders.models import Order, OrderMessage
from .db_service import create_notification_for_event
from .mail_service import (
    send_group_notification_email,
    send_order_notification_email,
    send_new_message_email,
)
from django.core.cache import cache

logger = logging.getLogger(__name__)
User = get_user_model()


def send_notifications_for_group_status_change(group):
    try:
        logger.info(f"🚀 為團購 '{group.name}' (狀態: {group.status}) 發送通知...")

        group_status_display = group.get_status_display()
        cache_key = f"in_app_notification:group_status:{group.id}:{group.status}"
        if cache.get(cache_key):
            logger.warning(f"已跳過重複的站內通知 (快取鍵: {cache_key})")
            return

        follower_ids = group.get_followers()
        all_user_ids = list(set(follower_ids + [group.owner_id]))

        if not all_user_ids:
            return

        title = f"【{group_status_display}】{group.name}"
        content = f"您參與的團購「{group.name}」狀態已更新為：{group_status_display}。"
        create_notification_for_event(group, all_user_ids, title, content)

        owner = group.owner
        if owner.is_verified:
            send_owner_email_task.delay(group.id, group_status_display)
        if follower_ids:
            send_followers_email_task.delay(group.id, group_status_display)
        logger.info(f"📧 團購狀態 '{group_status_display}' 的郵件任務已加入隊列。")
        cache.set(cache_key, True, timeout=60)

    except Exception as e:
        logger.error(
            f"❌ 發送團購狀態變更通知失敗 (Group ID: {group.id}): {e}", exc_info=True
        )


def send_notification_for_new_order(order):
    try:
        group = order.group
        if not group:
            return
        logger.info(f"🚀 為新訂單 ID:{order.id} 發送通知...")

        owner = group.owner
        title = f"【收到新訂單】{group.name}"
        content = f"您的團購收到一筆來自 {order.user.username} 的新訂單！"
        create_notification_for_event(group, [owner.id], title, content)

        if owner.is_verified:
            send_owner_email_task.delay(group.id, "團購收到新訂單", order_id=order.id)

    except Exception as e:
        logger.error(
            f"❌ 發送新訂單通知失敗 (Order ID: {order.id}): {e}", exc_info=True
        )


def send_notification_for_order_status_change(order, target_status_display):
    try:
        order = Order.objects.get(id=order.id)
        group = order.group
        owner = group.owner
        follower = order.user
        status_text = f"訂單「{target_status_display}」"

        title = f"【訂單狀態更新】{group.name}"
        content = f"您關於團購「{group.name}」的訂單，狀態已更新為：{target_status_display}。"

        if order.order_status in [
            Order.OrderStatus.PROCESSING,
            Order.OrderStatus.SHIPPED,
            Order.OrderStatus.COMPLETED,
        ]:
            logger.info(
                f"訂單 {order.id} 狀態更新為 {target_status_display}，準備通知團主與跟團者..."
            )

            cache_key = f"in_app_notification:order_status:{order.id}:{order.order_status}"
            if cache.get(cache_key):
                logger.warning(f"已跳過重複的訂單狀態站內通知 (快取鍵: {cache_key})")
            else:
                recipients_for_in_app = list({owner.id, follower.id})
                create_notification_for_event(
                    group, recipients_for_in_app, title, content, order=order
                )
                if owner.is_verified:
                    send_owner_email_task.delay(group.id, status_text, order_id=order.id)
                if owner.id != follower.id and follower.is_verified:
                    send_followers_email_task.delay(
                        group.id, status_text, order_id=order.id
                    )
                cache.set(cache_key, True, timeout=60)

    except Exception as e:
        logger.error(
            f"❌ 發送訂單狀態更新通知失敗 (Order ID: {order.id}): {e}", exc_info=True
        )


def send_notification_for_new_order_message(order_message):
    try:
        order = order_message.order
        sender = order_message.sender
        receiver = order_message.receiver

        if not receiver:
            logger.warning(
                f"新留言通知：收件人為空，無法發送。留言 ID: {order_message.id}"
            )
            return

        title = f"訂單 #{order.order_number} 有新留言"
        content = f"來自 {sender.username}：{order_message.content[:50]}..."

        create_notification_for_event(order.group, [receiver.id], title, content, order=order)

        if receiver.is_verified and receiver.email:
            send_order_message_email_task.delay(order_message.id)
            logger.info(
                f"📧 訂單 #{order.order_number} 新留言郵件任務已加入隊列給 {receiver.username}。"
            )

    except Exception as e:
        logger.error(
            f"❌ 發送訂單新留言通知失敗 (Message ID: {order_message.id}): {e}",
            exc_info=True,
        )


@shared_task(bind=True, max_retries=3)
def send_owner_email_task(self, group_id, status_text, order_id=None):
    cache_key = f"email_task:{self.name}:{group_id}:{order_id}:{status_text}"
    if cache.get(cache_key):
        logger.warning(f"已跳過重複的郵件任務 (快取鍵: {cache_key})")
        return

    try:
        group = Group.objects.get(id=group_id)
        owner = group.owner
        if owner and owner.is_verified:
            order = Order.objects.get(id=order_id) if order_id else None
            if order:
                send_order_notification_email([owner.email], order, status_text)
            else:
                send_group_notification_email([owner.email], group, status_text)
            logger.info(f"📧 已將給團主的「{status_text}」郵件任務執行完畢。")
            cache.set(cache_key, True, timeout=300)
        else:
            logger.warning(f"郵件任務未發送：團主 {owner.email if owner else 'N/A'} 未驗證或不存在。")
    except Group.DoesNotExist:
        logger.warning(f"郵件任務失敗：找不到團購 (ID: {group_id})，任務將不會重試。")
        return
    except Order.DoesNotExist:
        logger.warning(f"郵件任務失敗：找不到訂單 (ID: {order_id})，任務將不會重試。")
        return
    except Exception as exc:
        logger.error(f"❌ 團主郵件任務失敗: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=3)
def send_followers_email_task(self, group_id, status_text, order_id=None):
    cache_key = f"email_task:{self.name}:{group_id}:{order_id}:{status_text}"
    if cache.get(cache_key):
        logger.warning(f"已跳過重複的郵件任務 (快取鍵: {cache_key})")
        return

    try:
        group = Group.objects.get(id=group_id)
        order = None
        if order_id:
            order = Order.objects.get(id=order_id)
            followers = [order.user]
        else:
            follower_ids = group.get_followers()
            followers = User.objects.filter(id__in=follower_ids)

        verified_follower_emails = [f.email for f in followers if f.is_verified]
        if verified_follower_emails:
            if order:
                send_order_notification_email(
                    verified_follower_emails, order, status_text, is_bulk=True
                )
            else:
                send_group_notification_email(
                    verified_follower_emails, group, status_text, is_bulk=True
                )
            logger.info(f"📧 已將給跟團者的「{status_text}」郵件任務執行完畢。")
            cache.set(cache_key, True, timeout=300)
        else:
            logger.warning(f"郵件任務未發送：沒有已驗證的跟團者郵箱。")
    except Group.DoesNotExist:
        logger.warning(f"郵件任務失敗：找不到團購 (ID: {group_id})，任務將不會重試。")
        return
    except Order.DoesNotExist:
        logger.warning(f"郵件任務失敗：找不到訂單 (ID: {order_id})，任務將不會重試。")
        return
    except Exception as exc:
        logger.error(f"❌ 跟團者郵件任務失敗: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=3)
def send_order_message_email_task(self, order_message_id):
    cache_key = f"email_task:{self.name}:{order_message_id}"
    if cache.get(cache_key):
        logger.warning(f"已跳過重複的郵件任務 (快取鍵: {cache_key})")
        return

    try:
        order_message = OrderMessage.objects.get(id=order_message_id)
        receiver = order_message.receiver
        sender = order_message.sender
        order = order_message.order
        group_owner = order.group.owner

        receiver_is_owner = receiver == group_owner

        if receiver and receiver.is_verified and receiver.email:
            send_new_message_email(
                recipient_email=receiver.email,
                sender_username=sender.username,
                order_number=order.order_number,
                message_content=order_message.content,
                order_id=order.id,
                receiver_is_owner=receiver_is_owner,
            )
            logger.info(
                f"📧 已將訂單 #{order.order_number} 的新留言郵件任務執行完畢給 {receiver.username}。"
            )
            cache.set(cache_key, True, timeout=300)
        else:
            logger.warning(
                f"訂單 #{order.order_number} 新留言郵件任務：收件人 {receiver.username} 無效或未驗證。"
            )

    except Exception as exc:
        logger.error(
            f"❌ 訂單新留言郵件任務失敗 (Message ID: {order_message_id}): {exc}",
            exc_info=True,
        )
        raise self.retry(exc=exc, countdown=30)


@shared_task
def check_deadline():
    try:
        logger.info("🕐 定時任務: 開始檢查團購截止時間...")
        with transaction.atomic():
            expired_groups = Group.objects.select_for_update(skip_locked=True).filter(
                status="ongoing",
                deadline__lt=timezone.now(),
            )
            expired_count = 0
            for group in expired_groups:
                try:
                    logger.info(f"⏰ 團購逾期: {group.name}")
                    group.expire()
                    expired_count += 1
                except Exception as e:
                    logger.error(f"❌ 處理逾期團購失敗: {group.name} - {e}")

        if expired_count > 0:
            logger.info(f"🎉 截止時間檢查完成 - 處理了 {expired_count} 個逾期團購")
        else:
            logger.info("🎉 截止時間檢查完成 - 沒有需要處理的逾期團購")

    except Exception as e:
        logger.error(f"❌ 檢查截止時間任務失敗: {str(e)}")
