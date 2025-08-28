from django.db import models
from django.core.validators import MinValueValidator
from users.models import User, UserAddress
from groups.models import Group, JoinedGroup
from django.utils import timezone
import uuid


class Order(models.Model):
    number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    group = models.ForeignKey(Group, on_delete=models.PROTECT)
    joined_group = models.OneToOneField(JoinedGroup, on_delete=models.PROTECT)

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, default="TWD")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "待付款"
        PAID = "paid", "已付款"
        FAILED = "failed", "付款失敗"

    payment_status = models.CharField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    shipping_address = models.ForeignKey(
        UserAddress, on_delete=models.PROTECT, null=True, blank=True
    )

    class OrderStatus(models.TextChoices):
        PROCESSING = "processing", "待出貨"
        SHIPPED = "shipped", "已出貨"
        COMPLETED = "completed", "已完成"

    order_status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        null=True,
        blank=True,
        default=None,
        help_text="付款完成後才會有訂單狀態",
    )

    shipped_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.number or f"訂單 #{self.id} 尚未生成編號"

    # 生成新的訂單號並儲存
    # 格式：日期 + UUID前8碼
    def generate_order_number(self):
        today = timezone.now().strftime('%Y%m%d')
        self.number = f"{today}{uuid.uuid4().hex[:8].upper()}"
        self.save()

    # 標記付款失敗並儲存
    def mark_payment_failed(self):
        self.payment_status = self.PaymentStatus.FAILED
        self.save()

    # 付款成功，轉為待處理並儲存
    def mark_as_paid(self):
        if self.payment_status == self.PaymentStatus.PENDING:
            self.payment_status = self.PaymentStatus.PAID
            self.order_status = self.OrderStatus.PROCESSING
            self.save()
            return True
        return False

    # 標記為已出貨並儲存
    def mark_as_shipped(self):
        if (
            self.payment_status == self.PaymentStatus.PAID
            and self.order_status == self.OrderStatus.PROCESSING
        ):
            self.order_status = self.OrderStatus.SHIPPED
            self.shipped_at = timezone.now()
            self.save()
            return True
        return False

    # 確認收貨，標記為已完成並儲存
    def mark_as_completed(self):
        if (
            self.payment_status == self.PaymentStatus.PAID
            and self.order_status == self.OrderStatus.SHIPPED
        ):
            self.order_status = self.OrderStatus.COMPLETED
            self.completed_at = timezone.now()
            self.save()
            return True
        return False

    @property
    def formatted_amount(self):
        return f"${self.amount:,.0f}"
