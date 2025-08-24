from django.contrib import admin
from django.urls import path
from . import views

app_name = "groups"

urlpatterns = [
    path('', views.index, name="index"),

    # 團購新增
    path('create_group', views.create_group, name="create_group"),
    # 團購列表
    path('read_group', views.read_group, name="read_group"),
    # 團購編輯
    path('edit_group/<int:id>', views.edit_group, name="edit_group"),
    # 團購刪除
    path('delete_group/<int:id>', views.delete_group, name="delete_group")
]
