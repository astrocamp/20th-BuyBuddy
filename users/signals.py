from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserAddress

User = settings.AUTH_USER_MODEL

@receiver(post_save, sender=User)
def create_user_address(sender, instance, created, **kwargs):
    if created:
        UserAddress.objects.create(user=instance, is_default=True)