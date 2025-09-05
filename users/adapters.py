from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        # 允許第三方登入創建新帳號
        return True
    
    def save_user(self, request, sociallogin, form=None):
        from users.models import User
        
        email = sociallogin.user.email
        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            sociallogin.connect(request, existing_user)
            
        else:
            user = super().save_user(request, sociallogin, form)
        
        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=["is_verified"])

        return user