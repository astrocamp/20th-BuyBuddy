import logging

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from anymail.message import AnymailMessage

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    def add_message(
        self,
        request,
        level,
        message_template=None,
        message_context=None,
        extra_tags="",
        message=None,
    ):
        # 攔截預設 messages 模版
        if message_template == "account/messages/logged_in.txt":
            return ImmediateHttpResponse()


def send_password_reset_email_with_template(email: str, reset_url: str):
    template_name = "重設密碼信"
    if not template_name:
        logger.error(
            "Mailgun password reset template name is not configured in settings."
        )
        return

    try:
        msg = AnymailMessage(
            template_id=template_name,  # 使用您在 settings 中定義的模板名稱
            to=[email],
            from_email=settings.DEFAULT_FROM_EMAIL,
        )
        # 將 reset_url 傳遞給模板中的 {{reset_url}} 變數
        msg.merge_global_data = {
            "reset_url": reset_url,
        }
        msg.send()
    except Exception as e:
        logger.exception(f"寄送重設密碼信時發生錯誤: {e}")
        return False


class CustomAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        # 判斷是否為密碼重設信件
        if template_prefix == "account/email/password_reset_key":
            reset_url = context.get("password_reset_url")
            if reset_url:
                # 如果是，就呼叫我們新的、風格一致的函數
                send_password_reset_email_with_template(email, reset_url)
            else:
                logger.warning(
                    "password_reset_url not found in context for password reset email."
                )
                super().send_mail(template_prefix, email, context)
        else:
            # 其他所有信件（如帳號驗證信）都使用 allauth 的預設方法
            super().send_mail(template_prefix, email, context)

    def is_open_for_signup(self, request):
        return False


    # 自定義登入後的 行為
    def post_login(self, request, user, **kwargs):
        # 檢查登入來源並顯示對應訊息
        if request.session.get("is_social_signup"):
            # 註冊路線
            messages.success(request, f"註冊成功")
            del request.session["is_social_signup"]
        else:
            # 傳統登入
            messages.success(request, f"登入成功")

        return redirect("/")


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        # 允許第三方登入創建新帳號
        return True

    # 自定義第三方登入註冊的 行為
    def save_user(self, request, sociallogin, form=None):
        from users.models import User

        # 取得第三方登入的 email
        email = sociallogin.user.email
        # 過濾出 相同的 email
        existing_user = User.objects.filter(email=email).first()
        # 如果有 相同的 email
        if existing_user:
            if not existing_user.is_verified:
                messages.error(request, "此信箱已經註冊過，請先驗證信箱")
                raise ImmediateHttpResponse(redirect("users:sessions_new"))
            # 連結第三方登入的帳號
            # 手動建立 SocialAccount 連結
            from allauth.socialaccount.models import SocialAccount

            social_account, created = SocialAccount.objects.get_or_create(
                user=existing_user,
                provider=sociallogin.account.provider,
                uid=sociallogin.account.uid,
                defaults={"extra_data": sociallogin.account.extra_data},
            )
            sociallogin.user = existing_user
            user = existing_user

            if sociallogin.account.provider == 'line':
                user.line_id = sociallogin.account.uid
                user.save(update_fields=["line_id"])
        # 如果沒有 相同的 email
        else:
            request.session["is_social_signup"] = True
            
            # 創建新帳號，讓 allauth 完成註冊流程
            user = super().save_user(request, sociallogin, form)

        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=["is_verified"])

        return user
