from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("payment/request/<int:group_id>/", views.request, name="request"),
    path("payment/confirm/", views.confirm, name="confirm"),
    path("payment/cancel/", views.cancel, name="cancel"),
    path("test/", views.test, name="test"),
]
