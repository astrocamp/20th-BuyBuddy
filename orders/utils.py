from django.shortcuts import get_object_or_404
from .models import Order
from groups.models import Group, JoinedGroup
from products.models import JoinedGroupProduct
from django.db.models import Sum, F, Prefetch, Q


# 查詢跟團者資訊
def get_buyer_list_data(user, group_id, for_export=False):
    group = get_object_or_404(Group, id=group_id, owner=user)

    orders = []
    buyers = []

    if group.status == "ongoing":
        # 團購進行中，顯示跟團者

        if not for_export:
            # 匯出 excel 的時候不需要查未成團訂單
            buyers = (
                JoinedGroup.objects.filter(group_id=group_id, group__status="ongoing")
                .select_related("buyer")
                .prefetch_related(
                    "joined_group_products__product",
                )
                .annotate(
                    total_amount=Sum(
                        F('joined_group_products__product__price')
                        * F('joined_group_products__quantity')
                    )
                )
            )

    else:
        # 團購已達標或其他狀態，顯示訂單
        # 匯出 excel ，顯示訂單
        orders = (
            Order.objects.filter(group_id=group_id, group__status="reached")
            .select_related("joined_group", "user", "group")
            .prefetch_related(
                Prefetch(
                    "joined_group__joined_group_products",
                    queryset=JoinedGroupProduct.objects.select_related(
                        "product"
                    ).filter(deleted_at__isnull=True),
                )
            )
            .annotate(
                total_amount=Sum(
                    F('joined_group__joined_group_products__product__price')
                    * F('joined_group__joined_group_products__quantity'),
                    filter=Q(
                        joined_group__joined_group_products__deleted_at__isnull=True
                    ),
                )
            )
        )

    return group, orders, buyers
