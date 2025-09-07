from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    製作專屬 Email 的 token 方法
    """

    def _make_hash_value(self, user, timestamp):
        """
        只使用用戶 ID、密碼、電子郵件和時間
        不用 last_login，配合我們註冊成功即登入的流程
        """
        return f"{user.pk}{user.password}{timestamp}{user.email}"


# 創建一個此類的實例，供視圖使用
email_verification_token_generator = EmailVerificationTokenGenerator()
