from django.shortcuts import render
from products.models import Product, ProductImage
from django.db.models import Prefetch, Count


def index(request):
    return render(request, "status/index.html")


def in_progress_list(request):
    products = (
        Product.objects.filter(group__status="ongoing")
        .select_related("group")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("order"))
        )
        .annotate(member_count=Count("group__joinedgroup"))
    )
    return render(request, "status/in_progress_list.html", {"products": products})


def ended_list(request):
    products = (
        Product.objects.filter(group__status__in=["reached", "failed"])
        .select_related("group")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("order"))
        )
    )

    return render(request, "status/ended_list.html", {"products": products})
