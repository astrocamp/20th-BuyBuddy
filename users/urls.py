from django.contrib import admin
from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("detail/", views.detail, name="detail"),
    path("new/", views.new, name="new"),
    path("", views.create, name="create"),
    path("sessions/new/", views.sessions_new, name="sessions_new"),
    path("sessions/delete/", views.sessions_delete, name="sessions_delete"),
    path("sessions/", views.sessions_create, name="sessions_create"),
]
