import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_fsm.signals import post_transition
from django.db import transaction
from groups.models import Group, JoinedGroup
from orders.models import Order, OrderMessage
from .services.base import (
    send_notifications_for_group_status_change,
    send_notification_for_new_order,
    send_notification_for_order_status_change,
    send_notification_for_new_order_message,
)

logger = logging.getLogger(__name__)

@receiver(post_transition, sender=Group)
def on_group_status_change(sender, instance, name, source, target, **kwargs):
    if target in ["reached", "failed", "deleted"]:
        logger.info(f"偵測到團購 '{instance.name}' 狀態變更: {source} → {target}。")
        send_notifications_for_group_status_change(instance)

@receiver(post_save, sender=JoinedGroup)
def handle_member_join_and_check_goal(sender, instance, created, **kwargs):
    if not created:
        return

    group = instance.group
    if group.status != "ongoing":
        return

    try:
        with transaction.atomic():
            group_to_check = Group.objects.select_for_update().get(id=group.id)
            if group_to_check.status != "ongoing":
                return

            if group_to_check.goal_choice == "quantity":
                count = JoinedGroup.objects.filter(
                    group=group_to_check,
                    deleted_at__isnull=True,
                ).count()

                if count >= group_to_check.min_goal: 
                    logger.info(
                        f"團購 '{group_to_check.name}' 已達人數目標 ({count}/{group_to_check.min_goal})。"
                    )
                    group_to_check.reached()

    except Exception as e:
        logger.error(f"處理 JoinedGroup 信號時發生未預期錯誤: {e}", exc_info=True)

@receiver(post_transition, sender=Order)
def on_order_status_change(sender, instance, name, source, target, **kwargs):
    logger.info(f"偵測到訂單 ID:{instance.id} 狀態變更: {source} → {target}。")
    send_notification_for_order_status_change(instance)

@receiver(post_save, sender=Order)
def handle_new_order_creation(sender, instance, created, **kwargs):
    if created:
        if instance.group and instance.group.status == "reached":
            logger.info(f"偵測到已達標團購的新訂單: ID {instance.id}。")
            send_notification_for_new_order(instance)

@receiver(post_save, sender=OrderMessage)
def handle_new_order_message(sender, instance, created, **kwargs):
    if created:
        logger.info(f"偵測到訂單 ID:{instance.order.id} 的新留言。")
        send_notification_for_new_order_message(instance)