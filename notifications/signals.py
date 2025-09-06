from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import GroupStatus
from .tasks import trigger_notification_task


@receiver(post_save, sender=GroupStatus)
def on_status_change(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.status in ["reached", "failed", "deleted"]:
        trigger_notification_task.delay(instance.group_id, instance.status)