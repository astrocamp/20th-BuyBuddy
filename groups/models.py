from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from users.models import User
from tinymce.models import HTMLField
from django_fsm import FSMField, transition


class Group(models.Model):
    GOAL_CHOICES = [
        ("quantity", "數量目標"),
        ("amount", "金額目標"),
    ]

    STATUS_CHOICES = [
        ("pending", "準備中"),
        ("ongoing", "進行中"),
        ("reached", "已達標"),
        ("failed", "已失敗"),
        ("deleted", "已取消"),
    ]

    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    min_goal = models.IntegerField()
    goal_choice = models.CharField(max_length=10, choices=GOAL_CHOICES)
    deadline = models.DateTimeField(null=True)
    current_progress = models.IntegerField(default=0)
    status = FSMField(default="pending", choices=STATUS_CHOICES, protected=True)
    banner = models.ImageField(upload_to="groups/banners/")
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True)
    description = HTMLField()
    total = models.IntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return self.name

    def _get_participant_user_ids(self):
        # 依據你的資料約束：owner 不會在這個名單裡
        return list(
            self.joinedgroup_set.exclude(buyer_id=self.owner_id)
            .values_list("buyer_id", flat=True)
            .distinct()
        )

    def _notify_status_change(self):
        from notifications.services import service as notification_service

        # 通知開團者
        notification_service.send_notification(user_id=self.owner_id, group=self)

        # 直接通知所有參與者（不需要再排除 owner）
        participant_ids = self._get_participant_user_ids()
        if participant_ids:
            notification_service.send_bulk_notifications(
                user_ids=participant_ids, group=self
            )

    @transition(field=status, source="pending", target="ongoing")
    def start_group(self):
        self._notify_status_change()

    @transition(field=status, source="ongoing", target="reached")
    def reach(self):
        from orders.services import create_orders

        create_orders(self)
        self._notify_status_change()

    @transition(field=status, source="ongoing", target="failed")
    def expire(self):
        self._notify_status_change()

    @transition(field=status, source=["pending", "ongoing"], target="deleted")
    def cancel_group(self):
        self._notify_status_change()


class JoinedGroup(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["buyer"]),
            models.Index(fields=["group"]),
            models.Index(fields=["-created_at"]),
            # 若多用到「有效的參團」（未軟刪），可以加條件索引
            models.Index(
                fields=["group", "buyer"],
                name="idx_group_buyer_active",
                condition=Q(deleted_at__isnull=True),
            ),
        ]
        constraints = [
            # 同一個 group：同一個 buyer 只能有一筆「有效」(deleted_at is null)
            models.UniqueConstraint(
                fields=["group", "buyer"],
                condition=Q(deleted_at__isnull=True),
                name="uniq_active_buyer_per_group",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.buyer.username} joined {self.group.name}"

    def clean(self):
        # 擋 owner 參團（跨表檢查只能在應用層做）
        if self.group_id and self.buyer_id and self.buyer_id == self.group.owner_id:
            raise ValidationError("團主不能參加自己的團購")

    def save(self, *args, **kwargs):
        # 確保任何入口（admin/shell/service/fixtures）都會跑驗證
        self.full_clean()
        return super().save(*args, **kwargs)
