from django.db import models
from django.core.validators import MinValueValidator
from users.models import User, UserAddress
from groups.models import Group, JoinedGroup
from django.utils import timezone
import uuid


class OrderManager(models.Manager):
    def bulk_create(self, objs, *args, **kwargs):
        for obj in objs:
            if not obj.order_number:
                obj.generate_order_number()
        return super().bulk_create(objs, *args, **kwargs)


class Order(models.Model):
    order_number = models.CharField(max_length=50, unique=True, null=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    group = models.ForeignKey(Group, on_delete=models.PROTECT)
    joined_group = models.OneToOneField(JoinedGroup, on_delete=models.PROTECT)
    objects = OrderManager()

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, default="TWD")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    shipping_address = models.ForeignKey(
        UserAddress, on_delete=models.PROTECT, null=True, blank=True
    )

    class OrderStatus(models.TextChoices):
        PENDING = "pending", "待付款"
        PROCESSING = "processing", "待出貨"
        SHIPPED = "shipped", "已出貨"
        COMPLETED = "completed", "已完成"

    order_status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )

    def generate_order_number(self):
        # 生成新的訂單號，不儲存，交由呼叫端儲存
        # 格式：日期(年月日) + UUID前8碼
        today = timezone.now().strftime("%Y%m%d%H%M%S")
        self.order_number = f"{today}{uuid.uuid4().hex[:8].upper()}"

    def save(self, *args, **kwargs):
        if not self.pk or not self.order_number:
            self.generate_order_number()
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

    payment_status = models.CharField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_payment_number(self):
        # 生成新的付款號，不儲存，交由呼叫端儲存
        # 格式：日期 + UUID前8碼
        today = timezone.now().strftime("%Y%m%d%H%M%S")
        self.payment_number = f"{today}{uuid.uuid4().hex[:8].upper()}"

    def save(self, *args, **kwargs):
        if not self.pk or not self.payment_number:
            self.generate_payment_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"訂單 {self.order.id} - 付款編號：{self.payment_number}"
