from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # ========== 我的跟團訂單相關 ==========
    # 全部我的跟團訂單
    path("my-orders/", views.my_orders, name="my_orders"),
    # 未成團訂單
    path("my-orders/ongoing", views.ongoing, name="ongoing"),
    # 未付款訂單
    path("my-orders/pending", views.pending, name="pending"),
    # 已付款待出貨訂單
    path("my-orders/paid", views.paid, name="paid"),
    # 已出貨訂單
    path("my-orders/shipped", views.shipped, name="shipped"),
    # 已完成訂單
    path("my-orders/completed", views.completed, name="completed"),
    # ========== 付款相關 ==========
    # 請求付款
    path("my-orders/payment/request/<int:order_id>/", views.request, name="request"),
    # 付款確認
    path("my-orders/payment/confirm/", views.confirm, name="confirm"),
    # 取消付款
    path("my-orders/payment/cancel/", views.cancel, name="cancel"),
    # 確認收貨
    path("my-orders/received/<int:order_id>/", views.received, name="received"),
]
