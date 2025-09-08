from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # ========== 我的跟團訂單相關 ==========
    # 全部我的跟團訂單
    path("my-orders/", views.my_orders, name="my_orders"),
    path(
        "my-orders/tab-content/",
        views.my_orders_tab_content,
        name="my_orders_tab_content",
    ),
    # ========== 我開團的訂單相關 ==========
    # 全部我的開團訂單
    path("owned-orders/", views.owned_orders, name="owned_orders"),
    path(
        "owned-orders/tab-content/",
        views.owned_orders_tab_content,
        name="owned_orders_tab_content",
    ),
    # 跟團者列表
    path("owned-orders/buyer_list/<int:group_id>/", views.buyer_list, name="buyer_list"),
    
    # 確認收貨
    path("my-orders/<int:order_id>/received/", views.received, name="received"),

    # 確認出貨
    path("owned-orders/<int:order_id>/shipped", views.shipped, name="shipped"),

    # ========== 選擇收貨地址相關 ==========
    # 選擇地址
    path(
        "my-orders/<int:order_id>/ship_address/",
        views.ship_address,
        name="ship_address",
    ),
    # ========== 付款相關 ==========
    # 確認訂單資訊
    path(
        "my-orders/<int:order_id>/check_order/",
        views.check_order,
        name="check_order",
    ),
    # 請求付款
    path(
        "my-orders/<int:order_id>/payment/request/",
        views.request,
        name="payment_request",
    ),
    # 付款確認
    path("my-orders/payment/confirm/", views.confirm, name="payment_confirm"),
    # 取消付款
    path("my-orders/payment/cancel/", views.cancel, name="payment_cancel"),
    # 付款成功
    path("my-orders/payment/success/", views.success, name="payment_success"),
    # 付款失敗
    path("my-orders/payment/fail/", views.fail, name="payment_fail"),
]
