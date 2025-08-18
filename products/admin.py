from django.contrib import admin
from .models import Product, ProductImage, JoinedGroupProduct

admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(JoinedGroupProduct)
