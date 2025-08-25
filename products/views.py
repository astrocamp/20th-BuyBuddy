from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, F
from products.models import Product, JoinedGroupProduct
from .models import Product, ProductImage, Group
from .forms import ProductForm
from django.contrib import messages
from django.shortcuts import redirect


def index(request):
    products = Product.objects.prefetch_related("images").all()
    return render(request, "products/index.html", {"products": products})


def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related("group").prefetch_related("images"),
        pk=product_id,
    )
    return render(request, "products/product_detail.html", {"product": product})
