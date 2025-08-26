from django.db import models
from users.models import User

class SalesIndex(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column="owner_id",
        related_name="sales_items",
    )
    image = models.CharField(max_length=200, blank=True, null=True)
    target_condition = models.PositiveIntegerField()
    current_progress = models.PositiveIntegerField(default=0)
    deadline = models.DateField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    TARGET_STATUS_CHOICES = [
        ("ongoing", "ongoing"),
        ("deleted", "deleted"),
        ("failed", "failed"),
        ("opened", "opened"),
    ]
    target_status = models.CharField(
        max_length=20,
        choices=TARGET_STATUS_CHOICES,
        default="opened",
    )

    class Meta:
        db_table = "sales_index"
        managed = True
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["target_status"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def progress_percentage(self) -> float:
        if self.target_condition > 0:
            return min((self.current_progress / self.target_condition) * 100, 100)
        return 0

    @property
    def remaining_quantity(self) -> int:
        return max(0, self.target_condition - self.current_progress)

    @property
    def related_group(self):
        """找到對應的團購"""
        try:
            from groups.models import Group
            return Group.objects.filter(name=self.name, owner=self.owner).first()
        except:
            return None


class SalesPurchase(models.Model):
    sales_index = models.ForeignKey(
        SalesIndex,
        on_delete=models.DO_NOTHING,
        db_column="grouplist_id",
        related_name="purchases",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column="user_id",
        related_name="sales_purchases",
    )
    quantity = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ("ongoing", "ongoing"),
        ("deleted", "deleted"),
        ("failed", "failed"),
        ("opened", "opened"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="opened")

    class Meta:
        db_table = "sales_purchase"
        managed = True
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["sales_index"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-purchase_date"]),
        ]

    def __str__(self) -> str:
        return f"Purchase {self.pk} for {self.sales_index.name}"