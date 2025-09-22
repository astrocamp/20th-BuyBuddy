from django.urls import path, re_path
from . import views
from users.views import custom_password_reset_from_key
from users import social_oauth

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
    # Social OAuth2 第三方登入
    path("google_social-oauth2/", views.google_social_oauth2, name="google_social_oauth2"),
    path("line_social-oauth2/", views.line_social_oauth2, name="line_social_oauth2"),
    path("line_no_email/", views.line_no_email, name="line_no_email"),
    # JS API for Social OAuth2，為了獲得 Client ID 和 Client Secret
    path("js_google_client/", social_oauth.js_google_client, name="js_google_client"),
    path("js_line_client/", social_oauth.js_line_client, name="js_line_client"),
    # Error 錯誤處理
    path("error/", views.handle_error, name="handle_error"),
    # Password Reset
    re_path(
        r"^accounts/password/reset/key/(?:(?P<uid>[^/]+)-)?(?P<key>[^/]+)/$",
        custom_password_reset_from_key,
        name="account_reset_password_from_key",
    ),
]
