from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import UserNotification
from django.utils import timezone


@login_required
def open(request, id):
    un = get_object_or_404(UserNotification, pk=id, user=request.user)
    if not un.is_read:
        un.is_read = True
        un.read_at = timezone.now()
        un.save(update_fields=["is_read", "read_at"])

    notification_id = un.notification.group_id
    # TODO 需導向銷售頁面
    return redirect("groups:detail", notification_id)


@require_POST
@login_required
def read_all(request):
    now = timezone.now()
    UserNotification.objects.filter(user=request.user, is_read=False).update(
        is_read=True, read_at=now
    )

    next_url = request.POST.get("next", "/")
    return redirect(next_url)
