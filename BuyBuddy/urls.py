from django.urls import path, include

from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    path('tinymce/', include('tinymce.urls')),
    path('notifications/', include("notifications.urls")),
    path('groups/', include("groups.urls")),
    path('users/', include("users.urls")),
    path('', include("pages.urls")),
    path('orders/', include("orders.urls")),
    path('accounts/', include('allauth.urls')),
] + debug_toolbar_urls()
