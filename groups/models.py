from django.db import models
from users.models import User

class Group(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_groups")
    min_goal = models.IntegerField()
    goal_choice = models.CharField(max_length=10)
    deadline = models.DateTimeField(null=True)
    current_progress = models.PositiveIntegerField(default=0)   
    status = models.CharField(max_length=20)   
    banner = models.ImageField(upload_to='groups/banners/')
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True)
    description = models.TextField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["status"]),
        ]
    
    def __str__(self) -> str:
        return self.name

    @property
    def progress_percentage(self) -> float:
        if self.min_goal > 0:
            return min((self.current_progress / self.min_goal) * 100, 100)
        return 0
    
    @property
    def remaining_quantity(self) -> int:
        return max(0, self.min_goal - self.current_progress)


class JoinedGroup(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="joined_groups")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="members")
    quantity = models.PositiveIntegerField(default=1)  
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)     
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=20, default="pending")
    
    class Meta:
        indexes = [
        models.Index(fields=["buyer"]),
        models.Index(fields=["group"]),
        models.Index(fields=["status"]),
        models.Index(fields=["-created_at"]),
        ]
    
    def __str__(self) -> str:
        return f"{self.buyer.username} joined {self.group.name}"