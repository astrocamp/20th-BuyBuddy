from django.contrib import admin
from django.urls import path
from . import views

app_name = "groups"

urlpatterns = [
	path("upload/", views.upload_image, name="upload_image"),
    path("", views.index, name="index"),
	path('new/', views.new, name="new"),
    path("<int:id>/", views.detail, name="detail"),
	path("<int:id>/member/edit", views.update_quantity, name="update_quantity"),
	path("<int:id>/manage/", views.manage, name="manage"),
	path("<int:id>/manage/edit", views.manage_edit, name="manage_edit"),
	path("<str:filter_type>/", views.index, name="index_filtered"),
]
