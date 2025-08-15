from django.db import models
from users.models import User

class Notification(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()


class UserNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
