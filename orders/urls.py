from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # TODO 測試付款頁面
    path("checkout/", views.checkout, name="checkout"),
    path("payment/request/<int:group_id>/", views.request, name="request"),
    path("payment/confirm/", views.confirm, name="confirm"),
    path("payment/cancel/", views.cancel, name="cancel"),
    # DEVLOG 測試建立訂單路徑
    path("test/", views.test, name="test"),
]
