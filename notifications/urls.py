from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("<int:id>/", views.open, name="open"),
    path("read-all/", views.read_all, name="read_all"),
]
