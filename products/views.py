from django.shortcuts import render, get_object_or_404
from .models import Product, ProductImage


def index(request):
    products = Product.objects.prefetch_related("images").all()
    return render(request, "products/index.html", {"products": products})


def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    images = ProductImage.objects.filter(product=product)
    return render(
        request, "products/product_detail.html", {"product": product, "images": images}
    )
