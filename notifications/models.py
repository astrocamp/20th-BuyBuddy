from django.db import models
from users.models import User
from groups.models import Group


class Notification(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        related_name="notifications",
    )

    def __str__(self):
        return self.title


class UserNotification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_notifications",
    )
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "notification")

    def __str__(self):
        return f"{self.user} - {self.notification.title}"


class GroupStatus(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    status = models.CharField(
        max_length=20,
        choices=Group.STATUS_CHOICES
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-changed_at"]