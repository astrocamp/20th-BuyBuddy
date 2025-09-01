from django.contrib import admin
from django.urls import path
from . import views

app_name = "groups"

urlpatterns = [
    path("", views.index, name="index"),
    path("owned/",views.owned, name="owned"),
    path("followed/", views.followed, name="followed"),
    path("<int:id>/", views.detail, name="detail"),
	path("<int:id>/member/edit", views.update_quantity, name="update_quantity"),
	path("<int:id>/manage/", views.manage, name="manage"),
	path("<int:id>/manage/edit", views.manage_edit, name="manage_edit"),
    path('new/', views.new, name="new"),
	path('new/product-form/', views.add_product_form, name="add_product_form")
]
