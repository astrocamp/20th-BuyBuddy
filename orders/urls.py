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
    # 確認收貨
    path("my-orders/received/<int:order_id>/", views.received, name="received"),
    # ========== 付款相關 ==========
    # 請求付款
    path(
        "my-orders/payment/request/<int:order_id>/",
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
