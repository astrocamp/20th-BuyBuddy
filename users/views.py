from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_http_methods
from users.models import User, UserAddress
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from .forms import (
    UserForm,
    UserAddressForm,
    RegistrationForm,
    LoginForm,
    UserAddressFormSet,
)
from anymail.message import AnymailMessage
from django.core.exceptions import ValidationError
from django.db import transaction


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
    new_user_form = RegistrationForm(request.POST)
    if not new_user_form.is_valid():
        return render(request, "users/new.html", {"form": new_user_form})

    try:
        new_user = new_user_form.save()

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
        return render(request, "users/new.html", {"form": new_user_form})


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


# 查看個人頁面
@login_required
def profiles(request):
    user = request.user
    user_form = UserForm(instance=user)
    user_addresses = UserAddress.objects.filter(user=user).order_by(
        "-is_default", "-created_at"
    )

    user_address_forms = UserAddressFormSet(queryset=user_addresses)

    return render(
        request,
        "users/profiles_section.html",
        {"user_form": user_form, "user_address_forms": user_address_forms},
    )


# 編輯或更新個人資訊
@login_required
def profiles_edit(request):
    user = request.user

    # POST 請求，更新資訊
    if request.method == "POST":
        user_form = UserForm(request.POST, request.FILES, instance=user)
        if user_form.is_valid():
            user_form.save()
            updated_form = UserForm(instance=user)

            # 儲存成功，返回顯示模式
            context = {
                "user_form": updated_form,
                "message": "用戶資訊更新成功！",
                "type": "success",
                "show": True,
            }
            return render(
                request,
                "users/shared/profiles.html",
                context,
            )

        else:
            # 有錯誤，返回編輯模式並顯示錯誤
            context = {
                "user_form": user_form,
                "message": "更新發生錯誤，請稍後再試",
                "type": "error",
                "show": True,
            }
            return render(
                request,
                "users/shared/profiles.html",
                context,
            )

    # GET 請求，顯示編輯表單
    else:
        user_form = UserForm(instance=user)
        return render(
            request,
            "users/shared/profiles_edit.html",
            {"user_form": user_form},
        )


# 顯示編輯畫面或更新地址
@login_required
def address_edit(request, address_id):
    user = request.user
    address = get_object_or_404(UserAddress, pk=address_id, user=user)

    # POST 請求，更新地址
    if request.method == "POST":
        # 得到原本的預設狀態
        original_is_default = address.is_default

        # 處理表單
        user_address_form = UserAddressForm(request.POST, instance=address)
        if user_address_form.is_valid():
            try:
                # 保存地址
                user_address_form.save()

                # 檢查是否變成了預設地址
                if not original_is_default and address.is_default:
                    # 重新抓所有地址
                    user_addresses = UserAddress.objects.filter(user=user).order_by(
                        "-is_default", "-created_at"
                    )
                    all_address_forms = UserAddressFormSet(queryset=user_addresses)

                    # render 包含 OOB
                    return render(
                        request,
                        "users/shared/address_with_oob.html",
                        {
                            # "user_address_form": user_address_form,
                            "all_address_forms": all_address_forms,
                            "include_address_list_oob": True,
                            "message": "地址更新成功！",
                            "type": "success",
                            "show": True,
                        },
                    )

                # 預設沒動，只回更新的地址
                # 不包含 OOB 更新
                context = {
                    "user_address_form": user_address_form,
                    "message": "地址更新成功！",
                    "type": "success",
                    "show": True,
                    "include_address_list_oob": False,
                }
                return render(
                    request,
                    "users/shared/address.html",
                    context,
                )

            except ValidationError as e:
                context = {
                    "user_address_form": user_address_form,
                    "message": "; ".join(e.messages),
                    "type": "error",
                    "show": True,
                }
                return render(
                    request,
                    "users/shared/address_edit.html",
                    context,
                )

        else:
            # 有錯誤，回到編輯模式並顯示錯誤
            context = {
                "user_address_form": user_address_form,
                "message": "更新發生錯誤，請稍後再試",
                "type": "error",
                "show": True,
            }
            return render(
                request,
                "users/shared/address_edit.html",
                context,
            )

    # GET 請求，顯示編輯頁面
    else:
        user_address_form = UserAddressForm(instance=address)
        return render(
            request,
            "users/shared/address_edit.html",
            {"user_address_form": user_address_form},
        )


# 刪除地址
@require_http_methods(["DELETE"])
@login_required
def address_delete(request, address_id):
    user = request.user
    target_address = get_object_or_404(UserAddress, pk=address_id, user=user)

    try:
        target_address.delete()
        user_address_form = UserAddressForm(instance=target_address)
        context = {
            "user_address_form": user_address_form,
            "delete": True,
            "message": "地址刪除成功！",
            "type": "success",
            "show": True,
        }
        return render(request, "users/shared/address.html", context)

    except ValidationError as e:
        user_address_form = UserAddressForm(instance=target_address)
        context = {
            "user_address_form": user_address_form,
            "message": "; ".join(e.messages),
            "type": "error",
            "show": True,
        }
        return render(request, "users/shared/address.html", context)


@login_required
# 新增地址
def address_create(request):
    user = request.user

    # POST 請求，新增地址
    if request.method == "POST":
        address_form = UserAddressForm(request.POST)
        if address_form.is_valid():
            # 創建新地址
            new_address_form = address_form.save(commit=False)
            new_address_form.user = user
            new_address_form.save()
            messages.success(request, "新增地址成功")
            return redirect("users:profiles")
        else:
            context = {
                "user_address_form": address_form,
                "message": "地址資訊有誤，請稍後再試",
                "type": "error",
                "show": True,
            }
            return render(
                request,
                "users/shared/address_create.html",
                context,
            )

    # GET 請求，取得地址空表單
    else:
        blank_address_form = UserAddressForm()
        return render(
            request,
            "users/shared/address_create.html",
            {"user_address_form": blank_address_form},
        )
