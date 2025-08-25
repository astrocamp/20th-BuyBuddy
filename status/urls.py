from django.contrib import admin
from django.urls import path
from . import views

app_name = "status"

urlpatterns = [
    path("", views.index, name="index"),
    path("in-progress/", views.in_progress_list, name="in_progress_list"),
    path("ended/", views.ended_list, name="ended_list"),
]
