from django.urls import path, include
from django.conf import settings

from django.conf import settings
from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    path('tinymce/', include('tinymce.urls')),
    path('notifications/', include("notifications.urls")),
    path('groups/', include("groups.urls")),
    path('users/', include("users.urls")),
    path('', include("pages.urls")),
    path('orders/', include("orders.urls")),
    path('accounts/', include('allauth.urls')),
]


if settings.DEBUG:
    urlpatterns += debug_toolbar_urls()
