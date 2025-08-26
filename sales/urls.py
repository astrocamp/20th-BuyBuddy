from django.urls import path
from . import views

app_name = "sales"

urlpatterns = [
    path('', views.index, name="index"),
    path('my-group/', views.my_sales, name="my_group"),
    path('purchases/', views.purchase_list, name="purchases"),
]