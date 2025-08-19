from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from users.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_verification_mail(request, user, email):
    try:
        # 製作 token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # 製作驗證連結
        verify_url = request.build_absolute_uri(
            reverse("users:verify_email", kwargs={"uid": uid, "token": token})
        )

        # 發信
        html_message = render_to_string(
            "emails/verify_email.html", {"verify_url": verify_url}
        )
        plain_message = f"請點擊以下連結驗證您的信箱：{verify_url}"

        send_mail(
            subject="驗證您的信箱",
            message=plain_message,  # 純文字版本
            html_message=html_message,  # HTML 版本
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception:
        return False


@login_required
def detail(request):
    return render(request, "users/detail.html")


def new(request):
    if request.user.is_authenticated:
        messages.info(request, "您已經登入了")
        return redirect("pages:homepage")
    return render(request, "users/new.html")


@require_POST
def create(request):
    email = request.POST.get("email")
    password = request.POST.get("password")

    if not email or not password:
        messages.warning(request, "缺少註冊資料")
        return redirect("users:new")

    try:
        # 先建立用戶資料
        new_user = User.objects.create_user(
            username=email, email=email, password=password
        )

        # 寄信
        success = send_verification_mail(request, new_user, email)
        if not success:
            messages.warning(request, "寄送驗證信失敗，請登入後稍後再試")
            return redirect("users:sessions_new")
        return redirect("users:check_email")

    except IntegrityError:
        messages.error(request, "此 Email 已註冊")
        return redirect("users:new")

    except Exception as e:
        print(f"註冊時發生錯誤: {e}")
        messages.error(request, "註冊失敗，請稍後再試")
        return redirect("users:new")


def sessions_new(request):
    if request.user.is_authenticated:
        messages.info(request, "您已經登入了")
        return redirect("pages:homepage")
    if request.GET.get("next"):
        messages.warning(request, "請先登入，以繼續訪問頁面")
    return render(request, "users/sessions_new.html")


@require_POST
def sessions_create(request):
    email = request.POST.get("email")
    password = request.POST.get("password")
    remember_me = "remember_me" in request.POST

    if not email or not password:
        messages.warning(request, "缺少登入資料")
        return redirect("users:sessions_new")

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
        return redirect("pages:homepage")
    else:
        messages.error(request, "帳號或密碼錯誤")
        return redirect("users:sessions_new")


def sessions_delete(request):
    next_url = request.GET.get("next")
    if next_url and next_url.strip():
        logout(request)
        messages.success(request, "登出成功")
        return redirect(next_url)
    logout(request)
    messages.success(request, "登出成功")
    return redirect("pages:homepage")


def check_email(request):
    # TODO: 個人頁面需要二次驗證
    if request.user.is_authenticated:
        user = request.user

        if user.is_verified:
            messages.info(request, "您的信箱已經驗證過了")
            return redirect("users:detail")

        success = send_verification_mail(request, user, user.email)
        if not success:
            messages.warning(request, "寄送驗證信失敗，請稍後再試")
            return redirect("users:detail")

        messages.success(request, "驗證信已發送，請至您的信箱點擊驗證連結")
        return redirect("users:detail")

    return render(request, "users/check_email.html")


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
            return redirect("pages:homepage")
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
