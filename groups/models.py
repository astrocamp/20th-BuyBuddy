from django.db import models
from users.models import User

class Group(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_groups")
    min_amount = models.IntegerField(null=True, blank=True)
    min_quantity = models.IntegerField(null=True, blank=True)
    goal_choice = models.CharField(max_length=10)
    deadline = models.DateTimeField(null=True)
    status = models.CharField(max_length=20)
    banner = models.ImageField(upload_to='groups/banners/')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True)
    description = models.TextField(null=True)


class JoinedGroup(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True)
