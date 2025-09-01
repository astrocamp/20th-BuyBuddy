from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings
from .models import UserAddress, DefaultAddressRequiredError
from django.db import transaction

User = settings.AUTH_USER_MODEL


@receiver(post_save, sender=User)
def create_user_address(sender, instance, created, **kwargs):
    if created:
        UserAddress.objects.create(user=instance, is_default=True)


# 檢查有沒有其他預設
def _has_other_default(user, exclude_pk=None):
    qs = UserAddress.object.filter(user=user, is_default=True)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)

    return qs.exist()


# 檢查是不是唯一一筆預設
def _is_only_default(user, exclude):
    qs = UserAddress.objects.filter(user=user, is_default=True)
    return qs.count() == 1


@receiver(post_save, sender=UserAddress)
def ensure_default_on_update(sender, instance: UserAddress, **kwargs):

    # 檢查儲存的資料是否為預設
    if instance.is_default:
        # 是的話要把其他的預設拿掉
        with transaction.atomic():
            UserAddress.objects.filter(user=instance.user, is_default=True).exclude(
                pk=instance.pk
            ).update(is_default=False)

    else:
        # 不是的話檢查是否有其他預設
        if not _has_other_default(instance.user, exclude_pk=isinstance.pk):
            raise DefaultAddressRequiredError("使用者至少需要一個預設地址")


@receiver(pre_delete, sender=UserAddress)
def ensure_default_on_delete(sender, instance: UserAddress, **kwargs):
    if not _has_other_default(instance.user, exclude_pk=isinstance.pk):
        raise DefaultAddressRequiredError("刪除失敗，無法刪除最後一個預設地址")
