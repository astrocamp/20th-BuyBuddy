from django.db import transaction, IntegrityError
from django.db.models import Prefetch

from .models import Order
from groups.models import JoinedGroup
from products.models import JoinedGroupProduct


def create_orders(group):
    # 檢查團購是否已經有訂單
    exist_orders = Order.objects.filter(group=group)
    if exist_orders.exists():
        # DEVLOG
        print(f"該團購已經有{exist_orders.count()}筆訂單")
        return exist_orders

    # 抓到這筆團購的所有參團紀錄
    joined_groups = (
        JoinedGroup.objects.filter(group=group)
        .select_related("buyer")
        .prefetch_related(
            Prefetch(
                "joined_group_products",
                queryset=JoinedGroupProduct.objects.select_related("product").filter(
                    deleted_at__isnull=True
                ),
            )
        )
    )

    orders = []

    # 根據每筆參團紀錄找出跟團者、商品、價錢、數量
    for joined_group in joined_groups:
        # 找到跟團者
        buyer = joined_group.buyer

        subtotal = 0

        # 找出每個商品的名字、價錢、數量並統計
        for joined_group_product in joined_group.joined_group_products.all():
            price = joined_group_product.product.price
            quantity = joined_group_product.quantity
            subtotal += price * quantity

            # DEVLOG
            print(
                f"{joined_group_product.product.name} X {quantity}個 = {quantity*price}元"
            )

        order = Order(
            user=buyer, group=group, joined_group=joined_group, amount=subtotal
        )

        orders.append(order)

    try:
        with transaction.atomic():
            created_orders = Order.objects.bulk_create(orders)
            # DEVLOG
            print(f"建立訂單成功，建立了{len(orders)}筆訂單")
            return created_orders

    except IntegrityError as e:
        # DEVLOG
        print(e)
        print("建立訂單失敗")
        raise

    except Exception as e:
        # DEVLOG
        print(e)
        print("建立訂單失敗，發生其他錯誤")
        raise
