from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class DefaultAddressRequiredError(ValidationError):
    """當使用者將失去最後一個預設地址時拋出。"""

    pass


class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar_url = models.ImageField(upload_to='avatars/')
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def save(self, *args, **kwargs):
        if not self.pk:  # 只有新用戶才給預設頭像
            self.avatar_url = "avatars/avatar_default.png"
        super().save(*args, **kwargs)


class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    recipient_name = models.CharField(max_length=50, null=True)
    is_default = models.BooleanField(default=True)
    phone = models.CharField(max_length=20, null=True)
    postal_code = models.CharField(max_length=5, null=True)
    county = models.CharField(max_length=10, null=True)
    district = models.CharField(max_length=10, null=True)
    road = models.CharField(max_length=100, null=True)
    detail = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_default=True),
                name="unique_default_address_per_user",
            )
        ]
