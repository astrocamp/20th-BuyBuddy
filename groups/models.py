from django.db import models
from django.utils import timezone
from django_fsm import FSMField, transition
from users.models import User
from tinymce.models import HTMLField

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

    def get_followers(self):

        return list(
            JoinedGroup.objects.filter(
                group=self,
                deleted_at__isnull=True,
            )
            .exclude(buyer=self.owner)
            .values_list("buyer_id", flat=True)
        )

    @transition(field=status, source="pending", target="ongoing")
    def start_group(self):
        self.save()

    @transition(field=status, source="ongoing", target="reached")
    def reach(self):
        from orders.services import create_orders

        create_orders(self)
        self.save()

    @transition(field=status, source="ongoing", target="failed")
    def expire(self):
        self.save()

    @transition(field=status, source=["pending", "ongoing"], target="deleted")
    def cancel_group(self):
        self.save()

class JoinedGroup(models.Model):

    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["buyer"]),
            models.Index(fields=["group"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.buyer.username} joined {self.group.name}"