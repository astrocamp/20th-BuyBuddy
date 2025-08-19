from django.contrib import admin
from django.urls import path
from . import views

app_name = "groups"

urlpatterns = [
    path('', views.index, name="index"),
    path('upload', views.upload, name="upload"),
    path('create', views.create, name='create'),
    path('read', views.read, name='read'),
]
