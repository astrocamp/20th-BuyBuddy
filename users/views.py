from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from users.models import User, UserAddress
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from .forms import UserForm, UserAddressForm, RegistrationForm, LoginForm
from anymail.message import AnymailMessage


def send_verification_mail(request, user, email):
    try:
        # 製作 token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # 製作驗證連結
        verify_url = request.build_absolute_uri(
            reverse("users:verify_email", kwargs={"uid": uid, "token": token})
        )

        # 使用 anymail 發送模板郵件
        mail = AnymailMessage(
            template_id="註冊驗證信",
            to=[email],
        )

        # 設定模板變數
        mail.merge_global_data = {"verify_url": verify_url}

        mail.send()
        return True

    except Exception as e:
        print(f"寄送驗證信時發生錯誤: {e}")
        return False


def new(request):
    if request.user.is_authenticated:
        messages.info(request, "您已經登入了")
        return redirect("groups:index")
    form = RegistrationForm()
    return render(request, "users/new.html", {"form": form})


@require_POST
def create(request):
    form = RegistrationForm(request.POST)
    if not form.is_valid():
        return render(request, "users/new.html", {"form": form})

    try:
        # 先建立用戶資料
        new_user = form.save(commit=False)
        new_user.avatar_url = (
            'image/upload/v1755754867/avatars/tyzned8ajzgzeokgarve.png'
        )
        new_user.set_password(form.cleaned_data["password"])  # 手動雜湊密碼
        new_user.save()

        # 寄信
        success = send_verification_mail(request, new_user, new_user.email)
        if success:
            messages.success(
                request,
                "驗證信已發送，請至您的信箱點擊驗證連結",
                extra_tags="verify register",
            )
        else:
            messages.warning(
                request,
                "但驗證信發送失敗，請稍後至個人頁面驗證",
                extra_tags="verify register",
            )

        login(request, new_user)
        return redirect("groups:index")

    except Exception as e:
        print(f"註冊時發生錯誤: {e}")
        messages.error(request, "註冊失敗，請稍後再試")
        return render(request, "users/new.html", {"form": form})


def sessions_new(request):
    if request.user.is_authenticated:
        messages.info(request, "您已經登入了")
        return redirect("groups:index")
    if request.GET.get("next"):
        messages.warning(request, "請先登入，以繼續訪問頁面")

    form = LoginForm()
    return render(request, "users/sessions_new.html", {"form": form})


@require_POST
def sessions_create(request):
    form = LoginForm(request.POST)
    if not form.is_valid():
        return render(request, "users/sessions_new.html", {"form": form})

    email = form.cleaned_data.get("email")
    password = form.cleaned_data.get("password")
    remember_me = "remember_me" in request.POST

    user = authenticate(request, username=email, password=password)
    if user:
        login(request, user)

        if remember_me:
            request.session.set_expiry(60 * 60 * 24 * 10)

        next_url = request.POST.get("next")
        if next_url and next_url.strip():
            messages.success(request, "登入成功")
            return redirect(next_url)
        messages.success(request, "登入成功")
        return redirect("groups:index")

    else:
        messages.error(request, "帳號或密碼錯誤")
        return render(request, "users/sessions_new.html", {"form": form})


def sessions_delete(request):
    next_url = request.GET.get("next")
    if next_url and next_url.strip():
        logout(request)
        messages.success(request, "登出成功")
        return redirect(next_url)
    logout(request)
    messages.success(request, "登出成功")
    return redirect("groups:index")


@login_required
def check_email(request):
    # TODO: 個人頁面需要二次驗證
    user = request.user

    if user.is_verified:
        messages.info(request, "您的信箱已經驗證過了")
        return redirect("users:profiles")

    success = send_verification_mail(request, user, user.email)
    if success:
        messages.success(
            request,
            "請至您的信箱點擊驗證連結",
            extra_tags="verify profile",
        )
    else:
        messages.warning(
            request,
            "請稍後再試",
            extra_tags="verify profile",
        )

    return redirect("users:profiles")


def verify_email(request, uid, token):
    try:
        # 取得用戶
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)

        # 檢查 token 是否有效
        if default_token_generator.check_token(user, token):
            user.is_verified = True
            user.save()
            login(request, user)
            messages.success(request, "驗證信箱成功！")
            return redirect("groups:index")
        else:
            # token 無效（可能過期）
            messages.error(
                request, "驗證連結已過期。如果您已註冊，請登入後重新發送驗證信"
            )
            return redirect("users:sessions_new")

    # 處理 user 不存在、連結錯誤
    except (User.DoesNotExist, ValueError, TypeError):
        messages.error(request, "無效的驗證連結。如果您尚未註冊，請先註冊帳號")
        return redirect("users:new")

    except Exception:
        messages.error(request, "驗證發生錯誤，如果您已註冊，請登入後重新發送驗證信")
        return redirect("users:new")


@login_required
def profiles(request):
    user = request.user
    user_address = get_object_or_404(UserAddress, user=user)
    user_form = UserForm(instance=user)
    user_address_form = UserAddressForm(instance=user_address)
    if request.method == "POST":
        user_form = UserForm(request.POST, request.FILES, instance=user)
        user_address_form = UserAddressForm(request.POST, instance=user_address)
        if user_form.is_valid() and user_address_form.is_valid():
            user_form.save()
            user_address_form.save()
        else:
            print("-" * 10)
            print(user_form.errors)
        return redirect("users:profiles")

    return render(
        request,
        "users/profiles.html",
        {"user_form": user_form, "user_address_form": user_address_form},
    )


@login_required
def edit(request):
    user = request.user
    user_address = get_object_or_404(UserAddress, user=user)
    user_form = UserForm(instance=user)
    user_address_form = UserAddressForm(instance=user_address)
    return render(
        request,
        "users/edit.html",
        {"user_form": user_form, "user_address_form": user_address_form},
    )
