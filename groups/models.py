from django.db import models
from users.models import User
from tinymce.models import HTMLField


class Group(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    min_goal = models.IntegerField()
    goal_choice = models.CharField(max_length=10)
    deadline = models.DateTimeField(null=True)
    current_progress = models.IntegerField(default=0)
    status = models.CharField(max_length=20)
    banner = models.ImageField(upload_to='groups/banners/')
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


class JoinedGroup(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=["buyer"]),
            models.Index(fields=["group"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.buyer.username} joined {self.group.name}"

    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
