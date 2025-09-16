from django.contrib import admin
from django.urls import path
from . import views

app_name = "groups"

urlpatterns = [
	path("extract/", views.extract, name="extract"),
	path("upload/", views.upload_image, name="upload_image"),
    path("", views.index, name="index"),
    path("new/", views.new, name="new"),
    path("<int:id>/", views.detail, name="detail"),
    path("<int:id>/edit", views.manage_edit, name="manage_edit"),
    path("<str:filter_type>/", views.index, name="index_filtered"),
]
