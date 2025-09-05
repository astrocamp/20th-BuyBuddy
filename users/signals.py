from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.conf import settings
from .models import UserAddress, DefaultAddressRequiredError

User = settings.AUTH_USER_MODEL


@receiver(post_save, sender=User)
def create_user_address(sender, instance, created, **kwargs):
    if created:
        UserAddress.objects.create(user=instance, is_default=True)


# 檢查有沒有其他預設
def _has_other_default(user, exclude_pk=None):
    qs = UserAddress.objects.filter(user=user, is_default=True)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)

    return qs.exists()


@receiver(pre_save, sender=UserAddress)
def ensure_default_before_save(sender, instance: UserAddress, **kwargs):
    # 若將新的設為預設，先把其他預設拿掉
    if instance.is_default:
        qs = UserAddress.objects.filter(user=instance.user, is_default=True)
        if instance.pk:
            qs = qs.exclude(pk=instance.pk)
        qs.update(is_default=False)
    else:
        # 若這筆沒有要成為預設，但系統裡沒有其他預設，禁止儲存
        has_other = (
            UserAddress.objects.filter(user=instance.user, is_default=True)
            .exclude(pk=instance.pk)
            .exists()
        )
        if not has_other:
            from django.core.exceptions import ValidationError

            raise ValidationError("至少需要有一個預設地址")


@receiver(pre_delete, sender=UserAddress)
def ensure_default_on_delete(sender, instance: UserAddress, **kwargs):
    if not _has_other_default(instance.user, exclude_pk=instance.pk):
        raise DefaultAddressRequiredError("無法刪除預設地址")
