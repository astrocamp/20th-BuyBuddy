from django.shortcuts import render
from groups.models import Group


def homepage(request):
    groups = Group.objects.filter(status="ongoing")[:9]
    return render(request, "pages/home.html", {"groups": groups})
