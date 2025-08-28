from django.db import models
from groups.models import Group, JoinedGroup


class Product(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    description = models.TextField()

    @property
    def formatted_price(self):
        return f"${self.price:,.0f}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    url = models.ImageField(upload_to='groups/products')
    order = models.IntegerField()


class JoinedGroupProduct(models.Model):
    joined_group = models.ForeignKey(
        JoinedGroup, on_delete=models.CASCADE, related_name="joined_group_products"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    deleted_at = models.DateTimeField(null=True)

    @property
    def subtotal(self):
        return f"${self.product.price * self.quantity:,.0f}"
