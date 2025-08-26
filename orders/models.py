from django.db import models
from groups.models import Group, JoinedGroup
from django.utils import timezone
import uuid


class Order(models.Model):
    order_number = models.CharField(max_length=50, unique=True)
    group = models.ForeignKey(Group, on_delete=models.PROTECT)
    joined_group = models.ForeignKey(JoinedGroup, on_delete=models.PROTECT)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="TWD")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    payment_status = models.CharField(
        max_length=30,
        default="pending",
    )

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            # 生成唯一訂單號：日期 + UUID前8碼
            today = timezone.now().strftime('%Y%m%d')
            self.order_number = f"{today}{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
