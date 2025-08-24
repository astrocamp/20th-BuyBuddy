from django.urls import path
from . import views


app_name = "products"

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:product_id>/", views.product_detail, name="product_detail"),
    path("product_create/<int:group_id>", views.product_create, name="product_create"),
]
