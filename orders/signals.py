from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment


@receiver(post_save, sender=Payment)
def mark_others_payment_fail(sender, instance, created, **kwargs):
    if created:
        qs = Payment.objects.filter(
            order_id=instance.order_id, payment_status="pending"
        )

        if instance.pk:
            qs = qs.exclude(pk=instance.pk)

        qs.update(payment_status="failed")
