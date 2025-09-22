from django.http import JsonResponse
from django.conf import settings
import secrets
from urllib.parse import urlencode
from google_auth_oauthlib.flow import Flow
import requests
from allauth.socialaccount.models import SocialLogin, SocialAccount
from users.models import User
import random
from django.core.cache import cache
from anymail.message import AnymailMessage
from django.contrib import messages
from django.shortcuts import render
from allauth.socialaccount.helpers import complete_social_login
from allauth.exceptions import ImmediateHttpResponse


# === 給 JS fetch 的 API ===
# Google API
def js_google_client(request):
  return JsonResponse({
    "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
    "HOSTNAME": settings.HOSTNAME,
  })

# Line API
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
        "scope": "profile openid email",
        "state": state
    }

    auth_url = f"https://access.line.me/oauth2/v2.1/authorize?{urlencode(params)}"

    return JsonResponse({"auth_url": auth_url})

# === Google ===
# Google 處理授權碼
def google_code_handler(code):
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
    flow.redirect_uri = f"https://{settings.HOSTNAME}/users/google_social-oauth2/"

    # 用授權碼換取 token
    flow.fetch_token(code=code)

    return {
        "access_token": flow.credentials.token,
        "id_token": flow.credentials.id_token,
        "refresh_token": flow.credentials.refresh_token,
    }
# 用 token 取得用戶資料
def google_user_info(token):
  response = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {token}"},
    )

  if response.status_code != 200:
      raise Exception(f"取得用戶資料失敗: {response.status_code}")

  return response.json()


# === Line ===
# Line 處理授權碼
def line_code_handler(code):
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

  
  response = requests.post(post_url, data=data, headers=headers)
  if response.status_code != 200:
      raise Exception(f"取得用戶資料失敗: {response.status_code}")
      
  token_data = response.json()
  return {
      "success": True,
      "access_token": token_data["access_token"],
      "id_token": token_data["id_token"],
      "refresh_token": token_data["refresh_token"],
  }

# 解析 Line token
def line_token_parser(token):
  url = "https://api.line.me/oauth2/v2.1/verify"
  data = {
      "id_token": token["id_token"],
      "client_id": settings.LINE_LOGIN_CHANNEL_ID,
  }

  response = requests.post(url, data=data)
  
  if response.status_code != 200:
      raise Exception(f"解析 Line token 失敗: {response.status_code}")

  return response.json()
  
def check_verify_code(request, context, verify_code):
  
  # 檢查驗證碼是否輸入
  if verify_code:
      # 檢查驗證碼是否正確
      check = verify_email_code(context['email'], verify_code)
      # 如果 True 直接登入，False 則顯示錯誤訊息
      if check['success']:
          user_info = {
              "email": context['email'],
              "user_name": context['line_user_name'],
              "user_id": context['line_user_id']
          }
          del request.session["line_user_info"]
          social_login = create_social_login(user_info, 'line')
          raise ImmediateHttpResponse(complete_social_login(request, social_login))
      else:
          messages.error(request, check['message'])
          return render(request, "users/line_no_email.html", context)
  
  # 如果驗證碼未輸入，則顯示 verify_code_error 錯誤訊息
  else:
    context['verify_code_error'] = "請輸入驗證碼"
    raise ImmediateHttpResponse(render(request, "users/line_no_email.html", context))
  

def verify_email_code(input_email, verify_code):
  stored_code = cache.get(f"verify_code_{input_email}")
  if not stored_code:
    return {
      "success": False,
      "message": "驗證碼不存在或已過期"
    }
  
  if str(stored_code) == str(verify_code):
      # 驗證成功後刪除驗證碼
      cache.delete(f"verify_code_{input_email}")
      return {
        "success": True,
        "message": "驗證成功"
      }
  
  return {
    "success": False,
    "message": "驗證碼錯誤"
  }



def send_verify_code(request, email):
  verify_code = secrets.randbelow(900000) + 100000
    
    # 將驗證碼存到快取，5分鐘過期
  cache.set(f"verify_code_{email}", verify_code, timeout=300)
  
  try: 
      mail = AnymailMessage(template_id="信箱綁定驗證", to=[email])
      # 使用 merge_global_data 傳遞變數到 Mailgun 模板
      mail.merge_global_data = {
          "verify_code": verify_code,
      }
      mail.send()
      messages.success(request, "已發送驗證碼至信箱，請至信箱查看")
  except Exception as e:
      messages.error(request, "發送驗證碼時發生錯誤，請稍後再試")
      return False





# === 通用 ===
# 創建 SocialLogin
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
      social_login.account.uid = user_info.git("user_id")  # Line 用戶 ID
  
  social_login.account.extra_data = user_info

  # 創建 暫時的 User
  user = User()
  user.email = user_info.get("email")
  user.username = user_info.get("email")  # 用 email 作為 username
  user.is_verified = True

  if provider == 'line':
      user.line_id = user_info.get("user_id")
      user.is_verified = False

  # 關聯 User 和 SocialAccount
  social_login.user = user
  social_login.account.user = user

  return social_login