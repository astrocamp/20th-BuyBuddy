from django.shortcuts import render, get_object_or_404
from .models import Product, ProductImage, Group
from .forms import ProductForm
from django.contrib import messages
from django.shortcuts import redirect


def index(request):
    products = Product.objects.prefetch_related("images").all()
    return render(request, "products/index.html", {"products": products})


def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related("group").prefetch_related("images"), pk=product_id
    )
    return render(request, "products/product_detail.html", {"product": product})


def product_create(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if request.method == 'POST':
        product_form = ProductForm(request.POST)
        if product_form.is_valid():
            data = product_form.save(commit=False)
            data.group = group
            data.save()
            messages.success(request, "產品已建立")
            return redirect('products:index')
        else:
            print(product_form.errors)
            messages.warning(request, "欄位填寫有誤，請檢查後再試")
            return redirect('products:product_create', group_id)
    product_form = ProductForm()
    return render(request, "products/product_create.html", {"product_form": product_form})
