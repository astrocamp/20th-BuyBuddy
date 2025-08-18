from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST, require_http_methods
from users.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


def detail(request):
    return render(request, "users/detail.html")


def new(request):
    return render(request, "users/new.html")


@require_POST
def create(request):
    email = request.POST.get("email")
    password = request.POST.get("password")

    if not email or not password:
        return redirect("users:new")

    try:
        User.objects.create_user(username=email, email=email, password=password)
        return redirect("users:sessions_new")
    except Exception:
        return redirect("users:new")


def sessions_new(request):
    return render(request, "users/sessions_new.html")


@require_POST
def sessions_create(request):
    email = request.POST.get("email")
    password = request.POST.get("password")
    user = authenticate(request, username=email, password=password)

    if user:
        login(request, user)
        next_url = request.POST.get("next", "pages:homepage")
        print(next_url)
        return redirect(next_url)
    else:
        return redirect("users:sessions_new")


@require_http_methods(["DELETE"])
def sessions_delete(request):
    logout(request)
    return render(request, "shared/navbar.html")
