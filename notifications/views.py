from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import UserNotification
from django.utils import timezone
from orders.models import Order


@login_required
def open(request, id):
    un = get_object_or_404(UserNotification, pk=id, user=request.user)
    if not un.is_read:
        un.is_read = True
        un.read_at = timezone.now()
        un.save(update_fields=["is_read", "read_at"])

    notification = un.notification

    if notification.order:
        order = notification.order
        if request.user == order.group.owner:
            return redirect("orders:buyer_list", group_id=order.group.id)
        else:
            return redirect("orders:order_messages", order_id=order.id)

    if notification.group:
        group = notification.group
        if group.status == 'reached':
            if request.user == group.owner:
                return redirect("orders:buyer_list", group_id=group.id)
            else:
                try:
                    order = Order.objects.get(user=request.user, group=group)
                    return redirect("orders:order_messages", order_id=order.id)
                except Order.DoesNotExist:
                    return redirect("groups:detail", pk=group.id)
        else:
            return redirect("groups:detail", pk=group.id)

    return redirect("/")


@require_POST
@login_required
def read_all(request):
    now = timezone.now()
    UserNotification.objects.filter(user=request.user, is_read=False).update(
        is_read=True, read_at=now
    )

    next_url = request.POST.get("next", "/")
    return redirect(next_url)
