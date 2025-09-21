import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.http import require_POST, require_http_methods

from anymail.message import AnymailMessage
from google_auth_oauthlib.flow import Flow
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialLogin, SocialAccount

from users.models import User, UserAddress
from .forms import (
    UserForm,
    UserAddressForm,
    RegistrationForm,
    LoginForm,
    UserAddressFormSet,
    CustomResetPasswordFromKeyForm,
    LineNoEmailForm,
)
from .tokens import email_verification_token_generator
import requests, secrets, random
from urllib.parse import urlencode
from django.core.cache import cache

def custom_password_reset_from_key(request, uid=None, key=None):
    if request.method == "POST":
        form = CustomResetPasswordFromKeyForm(request.POST)
        if form.is_valid():
            form.save()  # 更新密碼
            messages.success(request, "密碼已重置成功")
            return redirect("account_login")  # 或你想要的頁面
    else:
        form = CustomResetPasswordFromKeyForm(initial={"uid": uid, "key": key})

    return render(
        request,
        "account/password_reset_from_key.html",
        {"form": form},
    )


def handle_error(request):
    error_messages = {
        "config_error": "系統配置載入失敗，請重整頁面後再試",
        "network_error": "網路連線異常，請檢查網路狀態",
        "unknown": "發生未知錯誤，請聯絡客服",
        "auth_failed": "登入取消，請稍後再試",
    }
    if request.GET.get("type") == "config_error":
        messages.error(request, error_messages["config_error"])
        return redirect("users:sessions_new")
    elif request.GET.get("type") == "network_error":
        messages.error(request, error_messages["network_error"])
        return redirect("users:sessions_new")
    elif request.GET.get("type") == "auth_failed":
        messages.info(request, error_messages["auth_failed"])
        return redirect("users:sessions_new")
    messages.error(request, error_messages["unknown"])
    return redirect("users:sessions_new")


def send_verification_mail(request, user, email):
    try:
        # 製作 token - 使用自定義的 token 生成器
        token = email_verification_token_generator.make_token(user)
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
        modal_content = (
            "驗證信已發送，請至您的信箱點擊驗證連結"
            if success
            else "驗證信發送失敗，請稍後至個人頁面再次驗證"
        )

        request.session["verify_email_modal"] = {
            "modalShow": True,
            "title": "註冊成功",
            "content": modal_content,
            "img": "assets/register.svg",
        }
        try:
            login(request, new_user)
            return redirect("pages:homepage")
        except Exception as login_error:
            print(f"登入發生錯誤: {login_error}")
            messages.error(request, "註冊成功，請重新登入")
            return redirect("users:sessions_new")

    except Exception as e:
        print(f"註冊時發生錯誤: {e}")
        messages.error(request, "註冊失敗，請稍後再試")
        return render(request, "users/new.html", {"form": new_user_form})


def sessions_new(request):
    if request.user.is_authenticated:
        messages.warning(request, "您已登入")
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
    if not request.user.is_authenticated:
        messages.warning(request, "您已登出")
        return redirect("pages:homepage")

    next_url = request.GET.get("next")
    if next_url and next_url.strip():
        logout(request)
        messages.success(request, "登出成功")
        return redirect(next_url)
    logout(request)
    messages.success(request, "登出成功")
    return redirect("groups:index")


@require_POST
@login_required
def check_email(request):
    # TODO 個人頁面需要二次驗證
    user = request.user

    if user.is_verified:
        messages.info(request, "您的信箱已經驗證過了")
        return redirect("users:profiles")

    success = send_verification_mail(request, user, user.email)

    modal_title = (
        "已寄送驗證信，請至您的信箱點擊驗證連結"
        if success
        else "寄送驗證信失敗，請稍後嘗試"
    )
    modal_img = "assets/send_success.svg" if success else "assets/fail.svg"

    request.session["verify_email_modal"] = {
        "modalShow": True,
        "title": modal_title,
        "img": modal_img,
    }

    return redirect("users:profiles")


def verify_email(request, uid, token):
    try:
        # 取得用戶
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)

        # 檢查 token 是否有效
        if email_verification_token_generator.check_token(user, token):
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

    # 取出寄信 modal 狀態
    verify_email_modal = request.session.pop("verify_email_modal", None)
    context = {
        "user_form": user_form,
        "user_address_forms": user_address_forms,
        "verify_email_modal": verify_email_modal,
    }
    return render(
        request,
        "users/profiles_section.html",
        context,
    )


# 編輯或更新個人資訊
@login_required
def profiles_edit(request):
    user = request.user

    if request.method == "POST":
        user_form = UserForm(request.POST, request.FILES, instance=user)

        if user_form.is_valid():
            user_form.save()
            updated_form = UserForm(instance=user)

            # 儲存成功
            messages.success(request, "用戶資訊更新成功")
            context = {
                "user_form": updated_form,
                "partial_msg_show": True,
            }
            return render(
                request,
                "users/shared/profiles.html",
                context,
            )

        # 有錯誤，返回編輯模式
        else:
            if "avatar_url" in user_form.errors:
                error_message = str(user_form.errors['avatar_url'])
                if "檔案太大" in error_message:
                    messages.warning(request, "檔案太大了，不能超過 1MB")
                else:
                    messages.warning(request, "檔案格式不支援")

            return render(
                request,
                "users/shared/profiles_edit.html",
                {
                    "user_form": user_form,
                    "partial_msg_show": True,
                },
            )

    # GET 請求，顯示編輯表單
    else:
        user_form = UserForm(instance=user)
        return render(
            request,
            "users/shared/profiles_edit.html",
            {"user_form": user_form},
        )


# 取消更新個人資訊
def profiles_edit_cancel(request):
    user_form = UserForm(instance=request.user)
    return render(
        request,
        "users/shared/profiles.html",
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

                    # 使用 Django 內置消息系統
                    messages.success(request, "地址更新成功！")

                    # render 包含 OOB
                    return render(
                        request,
                        "users/shared/address_with_oob.html",
                        {
                            "all_address_forms": all_address_forms,
                            "include_address_list_oob": True,
                            "partial_msg_show": True,
                        },
                    )

                # 預設沒動，只回更新的地址
                # 不包含 OOB 更新
                messages.success(request, "地址更新成功")

                context = {
                    "user_address_form": user_address_form,
                    "partial_msg_show": True,
                }
                return render(
                    request,
                    "users/shared/address.html",
                    context,
                )

            except ValidationError as e:
                messages.error(request, "; ".join(e.messages))

                context = {
                    "user_address_form": user_address_form,
                    "return_edit": True,
                    "partial_msg_show": True,
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
                "return_edit": True,
            }
            return render(request, "users/shared/address_edit.html", context)

    # GET 請求，顯示編輯頁面
    else:
        user_address_form = UserAddressForm(instance=address)
        return render(
            request,
            "users/shared/address_edit.html",
            {"user_address_form": user_address_form, "first_edit": True},
        )


# 刪除地址
@require_http_methods(["DELETE"])
@login_required
def address_delete(request, address_id):
    user = request.user
    target_address = get_object_or_404(UserAddress, pk=address_id, user=user)

    try:
        target_address.delete()
        messages.success(request, "地址刪除成功！")

        user_address_form = UserAddressForm(instance=target_address)
        context = {
            "user_address_form": user_address_form,
            "delete": True,
            "partial_msg_show": True,
        }
        return render(request, "users/shared/address.html", context)

    except ValidationError as e:
        messages.error(request, "; ".join(e.messages))

        user_address_form = UserAddressForm(instance=target_address)
        context = {
            "user_address_form": user_address_form,
            "partial_msg_show": True,
        }
        return render(request, "users/shared/address.html", context)


# 新增地址
@login_required
def address_create(request):
    user = request.user

    # 從 GET 或 POST 讀 order_id
    # GET 表示從選擇地址頁面要求新增地址空表單
    # POST 表示從選擇地址頁面要求新增地址並導向訂單確認頁
    order_id = (
        request.GET.get("order_id")
        if request.method == "GET"
        else request.POST.get("order_id")
    )

    # POST 請求，新增地址
    if request.method == "POST":
        address_form = UserAddressForm(request.POST)

        if address_form.is_valid():
            # 創建新地址
            new_address_form = address_form.save(commit=False)
            new_address_form.user = user
            new_address_form.save()

            # 代表是從選擇地址來的
            if order_id:
                # 轉址把 order 和 address 帶過去
                url = f"{reverse('orders:check_order', args=[order_id])}?address_id={new_address_form.id}"

                # 回覆帶 HX-Redirect
                response = HttpResponse("")
                response["HX-Redirect"] = url
                return response

            else:
                # 重新載入地址列表供 OOB 使用
                user_addresses = UserAddress.objects.filter(user=user).order_by(
                    "-is_default", "-created_at"
                )
                user_address_forms = UserAddressFormSet(queryset=user_addresses)

                messages.success(request, "地址新增成功！")

                context = {
                    "user_address_forms": user_address_forms,
                    "partial_msg_show": True,
                    "include_address_list_oob": True,
                }
                # 成功時關閉彈窗並使用 OOB 更新地址列表
                return render(
                    request,
                    "users/shared/address_create_success.html",
                    context,
                )
        else:
            # 表單驗證失敗時，需要回傳帶有錯誤訊息的彈窗
            return render(
                request,
                "users/shared/address_create.html",
                {
                    "user_address_form": address_form,
                },
            )

    # GET 請求，取得地址空表單
    else:
        blank_address_form = UserAddressForm()
        return render(
            request,
            "users/shared/address_create.html",
            {
                "user_address_form": blank_address_form,
                "order_id": order_id,
            },
        )


# 取消更新、取消新增
@login_required
def address_cancel(request, address_id):
    user = request.user

    # 代表是取消新增
    if address_id == 0:
        return HttpResponse("")
    address = get_object_or_404(UserAddress, pk=address_id, user=user)
    user_address_form = UserAddressForm(instance=address)

    return render(
        request, "users/shared/address.html", {"user_address_form": user_address_form}
    )


# Google OAuth2
# 回傳 Google Client ID
def js_google_client(request):
    return JsonResponse({
        "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
        "HOSTNAME": settings.HOSTNAME,
    })

# TODO: 接收前端的授權碼進行驗證和登入
def social_oauth2(request):
    # 先加入調試訊息
    code = request.GET.get("code")

    if not code:
        messages.error(request, "過程中斷，請重新嘗試")
        return redirect("users:sessions_new")

    try:
        # 處理 Google 授權碼，完成登入流程

        # 1. 用授權碼換取 access token
        tokens = token_code_handler(code)

        # 2. 用 access token 取得用戶資料
        user_info = get_user_info(tokens["access_token"])
        # 3. 前往登入或註冊
        social_login = create_social_login(user_info, 'google')
        return complete_social_login(request, social_login)
    except ImmediateHttpResponse:
        # 讓 allauth 的重導向正常通過
        raise
    except (ValueError, KeyError):
        messages.error(request, "Google 授權失敗，請稍後再試")
        return redirect("users:sessions_new")
    except requests.RequestException:
        messages.error(request, "網路連線失敗，請稍後再試")
        return redirect("users:sessions_new")
    except Exception:
        messages.error(request, "系統錯誤，請稍後再試")
        return redirect("users:sessions_new")


def token_code_handler(code):
    # 設定 OAuth 流程
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=[
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "openid",
        ],
    )

    # 設定重導向 URI（必須與 Google Console 設定一致）
    flow.redirect_uri = f"https://{settings.HOSTNAME}/users/social-oauth2/"

    # 用授權碼換取 token
    flow.fetch_token(code=code)

    return {
        "access_token": flow.credentials.token,
        "id_token": flow.credentials.id_token,
        "refresh_token": flow.credentials.refresh_token,
    }


def get_user_info(access_token):
    response = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if response.status_code != 200:
        raise Exception(f"取得用戶資料失敗: {response.status_code}")

    return response.json()


def create_social_login(user_info, provider):
    # 創建 SocialLogin
    social_login = SocialLogin()

    # 創建 SocialAccount
    social_login.account = SocialAccount()
    social_login.account.provider = provider
    
    # 根據不同的提供商設定 uid
    if provider == 'google':
        social_login.account.uid = user_info.get("sub")  # Google 用戶 ID
    elif provider == 'line':
        social_login.account.uid = user_info.get("line_user_id") or user_info.get("sub")  # Line 用戶 ID
    
    social_login.account.extra_data = user_info

    # 創建 暫時的 User
    user = User()
    user.email = user_info.get("email", "")
    user.username = user_info.get("email", "")  # 用 email 作為 username
    user.is_verified = True

    if provider == 'line':
        user.line_id = user_info.get("line_user_id") or user_info.get("sub")
        user.is_verified = False

    # 關聯 User 和 SocialAccount
    social_login.user = user
    social_login.account.user = user

    return social_login

# Line OAuth2
def js_line_client(request):
    # 使用 python 的 secrets 模組生成 state
    state = secrets.token_urlsafe(32)

    # 將生成的 state 存在 Django session 中
    request.session["line_oauth_state"] = state

    # 建構授權 URL
    params = {
        "response_type": "code",
        "client_id": settings.LINE_LOGIN_CHANNEL_ID,
        "redirect_uri": f"https://{settings.HOSTNAME}/users/line_social-oauth2/",
        # TODO: 加上 email 權限
        "scope": "profile openid",
        "state": state
    }
    auth_url = f"https://access.line.me/oauth2/v2.1/authorize?{urlencode(params)}"

    return JsonResponse({"auth_url": auth_url})

def line_social_oauth2(request):
    
    # 檢查 state 是否一致
    if request.GET.get("state") != request.session.get("line_oauth_state"):
        messages.error(request, "state 不一致，請重新嘗試")
        return redirect("users:sessions_new")
    
    # 檢查 code 是否存在
    code = request.GET.get("code")
    if not code:
        messages.error(request, "code 不存在，請重新嘗試")
        return redirect("users:sessions_new")
    
    # 清除 Django session 中的 state
    del request.session["line_oauth_state"]

    # 取得 Line token -> 往 get_line_token 函式
    line_token = get_line_token(code)

    if not line_token["success"]:
        messages.error(request, line_token["message"])
        return redirect("users:sessions_new")

    # 解析 Line token -> 往 parse_line_token 函式
    line_data = parse_line_token(line_token)

    # 檢查 Line token 是否解析成功
    if not line_data["success"]:
        messages.error(request, line_data["message"])
        return redirect("users:sessions_new")

    # 從 line data 中取得 user 資料
    user_info = line_data.get('data')

    if user_info.get('email'):
        social_login = create_social_login(user_info, 'line')
        return complete_social_login(request, social_login)

    # 假設 line 的 email 不存在，則跳轉到 line_no_email 頁面
    else:
        request.session["line_user_info"] = user_info
        return render(request, "users/line_no_email.html")

# 輸入信箱頁面
def line_no_email(request):
    form = LineNoEmailForm(request.POST)

    if "line_user_info" not in request.session:
          messages.error(request, "請先進行 Line 登入")
          return redirect("users:sessions_new")

    # 用戶輸入 email 並送出
    if request.method == "POST":
        input_email = request.POST.get("email")
        line_user_name = request.session["line_user_info"].get("name")
        line_user_id = request.session["line_user_info"].get("sub")
        verify_code = request.POST.get("verify_code")

        # 重發驗證碼
        if 'resend_code' in request.POST:
            send_code = send_verify_code(input_email)
            if send_code:
                messages.info(request, "已發送驗證碼至信箱，請至信箱查看")
            else:
                messages.error(request, "發送驗證碼時發生錯誤，請稍後再試")
            return render(request, "users/line_no_email.html", {
                "form": form, 
                "email": input_email, 
                "line_user_name": line_user_name,
                "line_user_id": line_user_id,
                "verify": True}
                )
            

        # 檢查 email 是否已註冊
        existing_email = User.objects.filter(email=input_email).first()

        # 如果 用戶輸入的 email 已註冊，則發送驗證碼至信箱
        if existing_email:

            # 檢查是否有驗證碼欄位，沒有欄位代表初次發送驗證碼
            if 'verify_code' in request.POST:
                # 檢查驗證碼是否輸入
                if verify_code:
                    # 檢查驗證碼是否正確
                    check_verify_code = verify_email_code(input_email, verify_code)

                    # 如果 True 直接登入，False 則顯示錯誤訊息
                    if check_verify_code[0]:
                        user_info = {
                            "email": input_email,
                            "line_user_name": line_user_name,
                            "line_user_id": line_user_id
                        }
                        del request.session["line_user_info"]
                        social_login = create_social_login(user_info, 'line')
                        return complete_social_login(request, social_login)
                    else:
                        messages.error(request, check_verify_code[1])
                        return render(request, "users/line_no_email.html", {
                            "form": form, 
                            "email": input_email, 
                            "line_user_name": line_user_name,
                            "line_user_id": line_user_id,
                            "verify": True,
                        })
                
                # 如果驗證碼未輸入，則顯示 verify_code_error 錯誤訊息
                else:
                    return render(request, "users/line_no_email.html", {
                        "form": form, 
                        "email": input_email, 
                        "line_user_name": line_user_name,
                        "line_user_id": line_user_id,
                        "verify": True,
                        "verify_code_error": "請輸入驗證碼"
                    })

            # 初次發送驗證碼
            send_code = send_verify_code(input_email)
            if send_code:
                messages.info(request, "已發送驗證碼至信箱，請至信箱查看")
            else:
                messages.error(request, "發送驗證碼時發生錯誤，請稍後再試")
            # 開啟 驗證碼欄位，讓用戶輸入驗證碼
            return render(request, "users/line_no_email.html", {
                "form": form, 
                "email": input_email, 
                "line_user_name": line_user_name,
                "line_user_id": line_user_id,
                "verify": True}
                )

        # 檢查信箱
        if not form.is_valid():
            return render(request, "users/line_no_email.html", {"form": form, "email": input_email})
        
        # 如果 用戶輸入的 email 不重複，則建立新的 user 並綁定 line
        user_info = {
            "email": input_email,
            "line_user_name": line_user_name,
            "line_user_id": line_user_id
        }
        social_login = create_social_login(user_info, 'line')
        return complete_social_login(request, social_login)
    # 進入 輸入信箱頁面
    return render(request, "users/line_no_email.html")

# 發送驗證碼
def send_verify_code(input_email):
    verify_code = random.randint(100000, 999999)
    
    # 將驗證碼存到快取，5分鐘過期
    cache.set(f"verify_code_{input_email}", verify_code, timeout=300)
    
    try: 
        mail = AnymailMessage(template_id="信箱綁定驗證", to=[input_email])
        # 使用 merge_global_data 傳遞變數到 Mailgun 模板
        mail.merge_global_data = {
            "verify_code": verify_code,
        }
        mail.send()
        return True
    except Exception as e:
        return False

# 驗證驗證碼
def verify_email_code(input_email, input_code):
    stored_code = cache.get(f"verify_code_{input_email}")
    
    if not stored_code:
        return False, "驗證碼不存在或已過期"
    
    if str(stored_code) == str(input_code):
        # 驗證成功後刪除驗證碼
        cache.delete(f"verify_code_{input_email}")
        return True, "驗證成功"
    
    return False, "驗證碼錯誤"

def get_line_token(code):
    post_url = "https://api.line.me/oauth2/v2.1/token"

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": f"https://{settings.HOSTNAME}/users/line_social-oauth2/",
        "client_id": settings.LINE_LOGIN_CHANNEL_ID,
        "client_secret": settings.LINE_LOGIN_CHANNEL_SECRET_KEY,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        response = requests.post(post_url, data=data, headers=headers)
        token_data = response.json()
        return {
            "success": True,
            "access_token": token_data["access_token"],
            "id_token": token_data["id_token"],
            "refresh_token": token_data["refresh_token"],
        }
    except Exception as e:
        message = f"取得 Line token 時發生錯誤: {e}"
        return {
            "success": False,
            "message": message
        }

def parse_line_token(token_data):
    url = "https://api.line.me/oauth2/v2.1/verify"
    data = {
        "id_token": token_data["id_token"],
        "client_id": settings.LINE_LOGIN_CHANNEL_ID,
    }

    try:
        response = requests.post(url, data=data).json()
        return {
            "success": True,
            "data": response
        }
    except Exception as e:
        message = f"解析 Line token 時發生錯誤: {e}"
        return {
            "success": False,
            "message": message
        }



def password_reset_redirect(request):
    return redirect("users:sessions_new")