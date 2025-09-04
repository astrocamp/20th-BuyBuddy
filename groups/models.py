from django.db import models
from users.models import User
from tinymce.models import HTMLField
from django_fsm import FSMField, transition
from django.db.models import Sum, F


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

    @transition(field=status, source="pending", target="ongoing")
    def start_group(self):
        """開始團購：開放參團"""
        pass

    @transition(field=status, source="ongoing", target="reached")
    def reach(self):
        """團購達標成功"""
        pass

    @transition(field=status, source="ongoing", target="failed")
    def expire(self):
        """團購逾期失敗"""
        pass

    @transition(field=status, source=["pending", "ongoing"], target="deleted")
    def cancel_group(self):
        """取消團購：由管理者或違規原因"""
        pass


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
        ]

    def __str__(self) -> str:
        return f"{self.buyer.username} joined {self.group.name}"

    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
