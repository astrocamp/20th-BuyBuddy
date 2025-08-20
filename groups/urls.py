from django.contrib import admin
from django.urls import path
from . import views

app_name = "groups"

urlpatterns = [
    path('', views.index, name="index"),

    # 團購新增
    path('create_group', views.create_group, name="create_group"),

    # 圖片上傳
    path('upload_img', views.upload_img, name="upload_img"),
    path('create_img', views.create_img, name='create_img'),
    path('read_img', views.read_img, name='read_img'),

]
