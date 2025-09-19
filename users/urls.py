from django.urls import path, re_path
from . import views
from users.views import custom_password_reset_from_key

app_name = "users"

urlpatterns = [
    path("profiles/", views.profiles, name="profiles"),
    path("profiles/edit/", views.profiles_edit, name="profiles_edit"),
    path(
        "profiles/edit/cancel/", views.profiles_edit_cancel, name="profiles_edit_cancel"
    ),
    path("profiles/address/create/", views.address_create, name="address_create"),
    path(
        "profiles/address/<int:address_id>/edit/",
        views.address_edit,
        name="address_edit",
    ),
    path(
        "profiles/address/<int:address_id>/delete/",
        views.address_delete,
        name="address_delete",
    ),
    path(
        "profiles/address/<int:address_id>/cancel/",
        views.address_cancel,
        name="address_cancel",
    ),
    path("new/", views.new, name="new"),
    path("", views.create, name="create"),
    path("sessions/new/", views.sessions_new, name="sessions_new"),
    path("sessions/delete/", views.sessions_delete, name="sessions_delete"),
    path("sessions/", views.sessions_create, name="sessions_create"),
    path(
        "password/reset/success/",
        views.password_reset_redirect,
        name="password_reset_success",
    ),
    path("check-email/", views.check_email, name="check_email"),
    path(
        "verify-email/<str:uid>/<str:token>/", views.verify_email, name="verify_email"
    ),
    path("social-oauth2/", views.social_oauth2, name="social_oauth2"),
    path("js_google_client/", views.js_google_client, name="js_google_client"),
    path("error/", views.handle_error, name="handle_error"),
    re_path(
        r"^accounts/password/reset/key/(?:(?P<uid>[^/]+)-)?(?P<key>[^/]+)/$",
        custom_password_reset_from_key,
        name="account_reset_password_from_key",
    ),
]
