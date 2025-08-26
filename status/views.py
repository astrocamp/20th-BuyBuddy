from django.shortcuts import render
from products.models import Product, JoinedGroupProduct
from django.db.models import Sum, F


def index(request):
    return render(request, "status/index.html")


def in_progress_list(request):
    products = (
        Product.objects.filter(group__status="進行中")
        .select_related("group")
        .prefetch_related("images")
    )
    for product in products:
        member_count = product.group.joinedgroup_set.count()

        product.group_status = {
            "member_count": member_count,
            "deadline": product.group.deadline,
        }
    return render(request, "status/in_progress_list.html", {"products": products})


def ended_list(request):
    products = (
        Product.objects.filter(group__status="已結束")
        .select_related("group")
        .prefetch_related("images")
    )

    for product in products:
        jgps = JoinedGroupProduct.objects.filter(joined_group__group=product.group)
        total_quantity = jgps.aggregate(total=Sum("quantity"))["total"] or 0
        total_amount = (
            jgps.aggregate(total=Sum(F("quantity") * F("product__price")))["total"] or 0
        )

        is_successful = False
        if (
            product.group.goal_choice == "quantity"
            and total_quantity >= product.group.min_goal
        ):
            is_successful = True
        elif (
            product.group.goal_choice == "amount"
            and total_amount >= product.group.min_goal
        ):
            is_successful = True

        product.final_status = "已達標" if is_successful else "失敗"

    return render(request, "status/ended_list.html", {"products": products})
