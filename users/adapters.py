from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect

class CustomAccountAdapter(DefaultAccountAdapter):
    def add_message(self, request, level, message_template=None, message_context=None, extra_tags="", message=None):
        # 攔截預設 messages 模版
        if message_template == "account/messages/logged_in.txt":
            return ImmediateHttpResponse()

        # 其他訊息使用原本的邏輯
        super().add_message(request, level, message_template, message_context, extra_tags, message)

    # 自定義登入後的 行為
    def post_login(self, request, user, **kwargs):
        # 檢查登入來源並顯示對應訊息
        if request.session.get('is_social_signup'):
            # 註冊路線
            messages.success(request, f"註冊成功")
            del request.session['is_social_signup']
        else:
            # 傳統登入
            messages.success(request, f"登入成功")

        return redirect('/')

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
                raise ImmediateHttpResponse(redirect('users:sessions_new'))
            # 連結第三方登入的帳號
            # 手動建立 SocialAccount 連結
            from allauth.socialaccount.models import SocialAccount
            social_account, created = SocialAccount.objects.get_or_create(
                user=existing_user,
                provider=sociallogin.account.provider,
                uid=sociallogin.account.uid,
                defaults={
                    'extra_data': sociallogin.account.extra_data
                }
            )
            sociallogin.user = existing_user
            user = existing_user
        # 如果沒有 相同的 email
        else:
            request.session['is_social_signup'] = True

            # 創建新帳號，讓 allauth 完成註冊流程
            user = super().save_user(request, sociallogin, form)
        
        return user