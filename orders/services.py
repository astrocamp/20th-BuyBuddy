from .models import Order
from groups.models import JoinedGroup
from django.db import transaction


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
        .prefetch_related("joined_group_products__product")
    )

    orders = []

    # 根據每筆參團紀錄找出跟團者、商品、價錢、數量
    for joined_group in joined_groups:
        # 找到跟團者
        buyer = joined_group.buyer

        # 找出商品們
        joined_group_products = joined_group.joined_group_products.all()

        subtotal = 0

        # 找出每個商品的名字、價錢、數量並統計
        for joined_group_product in joined_group_products:
            name = joined_group_product.product.name
            price = joined_group_product.product.price
            quantity = joined_group_product.quantity
            subtotal += price * quantity

            # DEVLOG
            print(f"{name} X {quantity}個 = {quantity*price}元")

        order = Order(
            user=buyer, group=group, joined_group=joined_group, amount=subtotal
        )

        orders.append(order)

    try:
        with transaction.atomic():
            Order.objects.bulk_create(orders)
            # DEVLOG
            print(f"建立訂單成功，建立了{len(orders)}筆訂單")
    except Exception as e:
        # DEVLOG
        print(e)
        print("建立訂單失敗")
