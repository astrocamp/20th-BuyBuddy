from django.contrib import admin
from django.urls import path, include
from groups import views

urlpatterns = [
    path('products/', include("products.urls")),
    path('sales/', include("sales.urls")),
    path('notifications/', include("notifications.urls")),
    path('status/', include("status.urls")),
    path('groups/', include("groups.urls")),
    path('users/', include("users.urls")),
    path('', views.index, name='homepage'),
    path('orders/', include("orders.urls")),
    path('admin/', admin.site.urls),
]
