from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar_url = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]


class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    recipient_name = models.CharField(max_length=50)
    is_default = models.BooleanField(default=False)
    phone = models.CharField(max_length=20)
    postal_code = models.CharField(max_length=5)
    county = models.CharField(max_length=10)
    district = models.CharField(max_length=10)
    road = models.CharField(max_length=100)
    detail = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
