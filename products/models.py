from tinymce.models import HTMLField
from django.db import models
from groups.models import Group, JoinedGroup


class Product(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    description = HTMLField()
    banner = models.ImageField(null=True, upload_to='products/banners/')


class JoinedGroupProduct(models.Model):
    joined_group = models.ForeignKey(
        JoinedGroup, on_delete=models.CASCADE, related_name="joined_group_products"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    deleted_at = models.DateTimeField(null=True)

    @property
    def subtotal(self):
        return self.product.price * self.quantity
