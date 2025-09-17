from django.shortcuts import render
from groups.models import Group


def homepage(request):
    groups = Group.objects.filter(status="ongoing")
    if request.user.is_authenticated:
        groups = groups.exclude(owner=request.user)
    groups = groups.order_by("-id")[:9]

    # 取出寄信 modal 狀態
    verify_email_modal = request.session.pop("verify_email_modal", None)

    return render(
        request,
        "pages/home.html",
        {"groups": groups, "verify_email_modal": verify_email_modal},
    )
