from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar_url = models.ImageField(upload_to='media/', null=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]


class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    recipient_name = models.CharField(max_length=50, null=True)
    is_default = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, null=True)
    postal_code = models.CharField(max_length=5, null=True)
    county = models.CharField(max_length=10, null=True)
    district = models.CharField(max_length=10, null=True)
    road = models.CharField(max_length=100, null=True)
    detail = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
