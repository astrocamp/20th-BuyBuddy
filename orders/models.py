from django.db import models
from django.core.validators import MinValueValidator
from users.models import User, UserAddress
from groups.models import Group, JoinedGroup
from django.utils import timezone
import uuid
from django_fsm import FSMField, transition


def _generate_unique_number():
    # 生成號碼，不儲存，交由呼叫端儲存
    # 格式：日期(年月日) + UUID前8碼
    today = timezone.now().strftime("%Y%m%d%H%M%S")
    return f"{today}{uuid.uuid4().hex[:8].upper()}"


class OrderManager(models.Manager):
    def bulk_create(self, objs, *args, **kwargs):
        for obj in objs:
            if not obj.order_number:
                obj.order_number = _generate_unique_number()
        return super().bulk_create(objs, *args, **kwargs)


class Order(models.Model):
    order_number = models.CharField(max_length=50, unique=True, null=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    group = models.ForeignKey(Group, on_delete=models.PROTECT)
    joined_group = models.OneToOneField(JoinedGroup, on_delete=models.PROTECT)
    objects = OrderManager()

    class OrderStatus(models.TextChoices):
        PENDING = "pending", "待付款"
        PROCESSING = "processing", "待出貨"
        SHIPPED = "shipped", "已出貨"
        COMPLETED = "completed", "已完成"

    order_status = FSMField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, default="TWD")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    shipping_address = models.ForeignKey(
        UserAddress, on_delete=models.PROTECT, null=True, blank=True
    )

    @transition(
        field=order_status, source=OrderStatus.PENDING, target=OrderStatus.PROCESSING
    )
    def mark_as_processing(self):
        """標記為待出貨"""
        pass

    @transition(
        field=order_status, source=OrderStatus.PROCESSING, target=OrderStatus.SHIPPED
    )
    def mark_as_shipped(self):
        """標記為已出貨"""
        pass

    @transition(
        field=order_status, source=OrderStatus.SHIPPED, target=OrderStatus.COMPLETED
    )
    def mark_as_completed(self):
        """標記為已完成"""
        pass

    def is_pending(self):
        """檢查訂單是否待付款"""
        return self.order_status == self.OrderStatus.PENDING

    def is_processing(self):
        """檢查訂單是否待出貨"""
        return self.order_status == self.OrderStatus.PROCESSING

    def is_shipped(self):
        """檢查訂單是否已出貨"""
        return self.order_status == self.OrderStatus.SHIPPED

    def is_completed(self):
        """檢查訂單是否已完成"""
        return self.order_status == self.OrderStatus.COMPLETED

    def save(self, *args, **kwargs):
        if not self.pk or not self.order_number:
            self.order_number = _generate_unique_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, null=False)
    payment_number = models.CharField(max_length=50, unique=True, null=False)

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "待付款"
        PAID = "paid", "已付款"
        FAILED = "failed", "付款失敗"

    payment_status = FSMField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @transition(
        field=payment_status, source=PaymentStatus.PENDING, target=PaymentStatus.PAID
    )
    def mark_as_paid(self):
        """標記為已付款"""
        pass

    @transition(
        field=payment_status, source=PaymentStatus.PENDING, target=PaymentStatus.FAILED
    )
    def mark_as_failed(self):
        """標記為付款失敗"""
        pass

    def is_pending(self):
        """檢查是否待付款"""
        return self.payment_status == self.PaymentStatus.PENDING

    def is_paid(self):
        """檢查是否已付款"""
        return self.payment_status == self.PaymentStatus.PAID

    def is_failed(self):
        """檢查是否付款失敗"""
        return self.payment_status == self.PaymentStatus.FAILED

    def save(self, *args, **kwargs):
        if not self.pk or not self.payment_number:
            self.payment_number = _generate_unique_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"訂單 {self.order.id} - 付款編號：{self.payment_number}"
