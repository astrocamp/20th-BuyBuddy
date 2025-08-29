from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # TODO 測試付款頁面
    path("checkout/", views.checkout, name="checkout"),
    # ===== 付款相關路徑 =====
    path("payment/request/<int:order_id>/", views.request, name="payment_request"),
    path("payment/confirm/", views.confirm, name="payment_confirm"),
    path("payment/cancel/", views.cancel, name="payment_cancel"),
    path("payment/success/", views.success, name="payment_success"),
    path("payment/fail/", views.fail, name="payment_fail"),
    # DEVLOG 測試建立訂單路徑
    path("test/", views.test, name="test"),
]
