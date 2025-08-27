from django.shortcuts import render
from products.models import Product, JoinedGroupProduct, ProductImage
from django.db.models import (
    Sum,
    F,
    Prefetch,
    Count,
    Q,
    Case,
    When,
    Value,
    CharField,
    IntegerField,
    Subquery,
    OuterRef,
)
from django.db.models.functions import Coalesce


def index(request):
    return render(request, "status/index.html")


def in_progress_list(request):
    products = (
        Product.objects.filter(group__status="進行中")
        .select_related("group")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("order"))
        )
        .annotate(member_count=Count("group__joinedgroup"))
    )
    return render(request, "status/in_progress_list.html", {"products": products})


def ended_list(request):
    quantity_subquery = (
        JoinedGroupProduct.objects.filter(joined_group__group_id=OuterRef("group_id"))
        .values("joined_group__group_id")
        .annotate(total_q=Sum("quantity"))
        .values("total_q")
    )

    amount_subquery = (
        JoinedGroupProduct.objects.filter(joined_group__group_id=OuterRef("group_id"))
        .values("joined_group__group_id")
        .annotate(total_a=Sum(F("quantity") * F("product__price")))
        .values("total_a")
    )

    products = (
        Product.objects.filter(group__status="已結束")
        .select_related("group")
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("order"))
        )
        .annotate(
            total_quantity=Coalesce(
                Subquery(quantity_subquery, output_field=IntegerField()), 0
            ),
            total_amount=Coalesce(
                Subquery(amount_subquery, output_field=IntegerField()), 0
            ),
        )
        .annotate(
            final_status=Case(
                When(
                    (
                        Q(group__goal_choice="quantity")
                        & Q(total_quantity__gte=F("group__min_goal"))
                    )
                    | (
                        Q(group__goal_choice="amount")
                        & Q(total_amount__gte=F("group__min_goal"))
                    ),
                    then=Value("已達標"),
                ),
                default=Value("失敗"),
                output_field=CharField(),
            )
        )
    )

    return render(request, "status/ended_list.html", {"products": products})
