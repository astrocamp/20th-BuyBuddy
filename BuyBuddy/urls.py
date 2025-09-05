from django.contrib import admin
from django.urls import path, include
from groups import views

urlpatterns = [
	path('admin/', admin.site.urls),
	path('tinymce/', include('tinymce.urls')),
    path('products/', include("products.urls")),
    path('sales/', include("sales.urls")),
    path('notifications/', include("notifications.urls")),
    path('status/', include("status.urls")),
    path('groups/', include("groups.urls")),
    path('users/', include("users.urls")),
    path('', include("pages.urls")),
    path('orders/', include("orders.urls")),
    path('accounts/', include('allauth.urls')),
]
