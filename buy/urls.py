from django.contrib import admin
from django.urls import path
from . import views

app_name = "buy"

urlpatterns = [
    path('purchase', views.purchase, name="purchase"),
    path('', views.index, name="index"),
]
