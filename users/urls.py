from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path('profiles/', views.profiles, name="profiles"),
    path('profiles/edit/', views.profiles_edit, name="profiles_edit"),
    path('profiles/address/create/', views.address_create, name="address_create"),
    path(
        'profiles/address/<int:address_id>/edit/',
        views.address_edit,
        name="address_edit",
    ),
    path(
        'profiles/address/<int:address_id>/delete/',
        views.address_delete,
        name="address_delete",
    ),
    path(
        'profiles/address/<int:address_id>/cancel/',
        views.address_cancel,
        name="address_cancel",
    ),
    path("new/", views.new, name="new"),
    path("", views.create, name="create"),
    path("sessions/new/", views.sessions_new, name="sessions_new"),
    path("sessions/delete/", views.sessions_delete, name="sessions_delete"),
    path("sessions/", views.sessions_create, name="sessions_create"),
    path("check-email/", views.check_email, name="check_email"),
    path(
        "verify-email/<str:uid>/<str:token>/", views.verify_email, name="verify_email"
    ),
]
