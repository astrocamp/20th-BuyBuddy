from django.urls import path
from . import views
from . import message_views

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
    path(
        "owned-orders/buyer_list/<int:group_id>/", views.buyer_list, name="buyer_list"
    ),
    # 確認收貨
    path("my-orders/<int:order_id>/received/", views.received, name="received"),
    # 確認出貨
    path("owned-orders/<int:order_id>/shipped/", views.shipped, name="shipped"),
    # 匯出跟團者資訊 Excel
    path(
        "owned-orders/buyer_list_export/<int:group_id>/",
        views.buyer_list_export,
        name="buyer_list_export",
    ),
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
        "my-orders/<int:order_id>/payment/linepay/",
        views.linepay,
        name="linepay",
    ),
    # 付款確認
    path("my-orders/payment/confirm/", views.confirm, name="payment_confirm"),
    # 取消付款
    path("my-orders/payment/cancel/", views.cancel, name="payment_cancel"),
    # 確認收貨
    path("my-orders/<int:order_id>/received/", views.received, name="received"),
    # ========== 訂單留言版相關 ==========
    # 跟團者留言板
    path(
        "my-orders/<int:order_id>/messages/",
        message_views.order_messages,
        name="order_messages",
    ),
    # 開團者留言板
    path(
        "owned-orders/<int:order_id>/messages/",
        message_views.group_owner_order_messages,
        name="group_owner_order_messages",
    ),
    # 新增留言
    path(
        "<int:order_id>/messages/send/",
        message_views.send_message,
        name="send_message",
    ),
    # 付款方式
    path(
        "my-orders/payment/type/<int:order_id>/",
        views.payment_type,
        name="payment_type",
    ),
    # 藍新金流
    path(
        "my-orders/payment/newebpay/<int:order_id>/",
        views.newebpay,
        name="newebpay",
    ),
    path(
        "my-orders/payment/newebpay/return/",
        views.newebpay_return,
        name="newebpay_return",
    ),
    path(
        "my-orders/payment/newebpay/notify/",
        views.newebpay_notify,
        name="newebpay_notify",
    ),
]
