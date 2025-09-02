from django.forms import (
    ModelForm,
    FileInput,
    TextInput,
    CheckboxInput,
    NumberInput,
    modelformset_factory,
)
from .models import User, UserAddress
from django import forms
from django.core.validators import MinLengthValidator
from django.contrib.auth.forms import UserCreationForm


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 幫密碼加上最小長度驗證器
        self.fields["password1"].validators.append(
            MinLengthValidator(8, message="密碼至少需要 8 個字符")
        )

        self.fields["password1"].min_length = 8

        # 自定義錯誤訊息
        self.fields["username"].error_messages = {
            "required": "請輸入用戶名",
            "unique": "此用戶名已被使用，請選擇其他用戶名",
            "invalid": "用戶名只能包含字母、數字和符號 @.+-_",
        }
        self.fields["email"].error_messages = {
            "required": "請輸入電子郵件地址",
            "invalid": "請輸入有效的電子郵件地址",
            "unique": "此 Email 已被註冊，請使用其他信箱",
        }
        self.fields["password1"].error_messages = {
            "required": "請輸入密碼",
            "password_too_short": "密碼太短",
            "password_too_common": "密碼過於常見",
            "password_entirely_numeric": "密碼不能完全是數字",
        }
        self.fields["password2"].error_messages = {
            "required": "請再次輸入密碼",
        }

        self.error_messages = {
            'password_mismatch': "兩次輸入的密碼不一致",
        }


class LoginForm(forms.Form):
    email = forms.EmailField(
        error_messages={
            "required": "請輸入電子郵件地址。",
            "invalid": "請輸入有效的電子郵件地址。",
        }
    )

    password = forms.CharField(
        error_messages={
            "required": "請輸入密碼。",
        }
    )


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ["avatar_url", "username"]
        labels = {
            "avatar_url": "大頭照",
            "username": "用戶名稱",
        }
        widgets = {
            "avatar_url": FileInput(
                attrs={"@change": "handleFile($event)", "accept": "image/*"}
            ),
            "username": TextInput(),
        }


class UserAddressForm(ModelForm):
    class Meta:
        model = UserAddress
        fields = [
            "recipient_name",
            "is_default",
            "phone",
            "postal_code",
            "county",
            "district",
            "road",
            "detail",
        ]
        labels = {
            "recipient_name": "收件人姓名",
            "is_default": "設爲預設",
            "phone": "收件人手機",
            "postal_code": "郵遞區號",
            "county": "城市/縣",
            "district": "區",
            "road": "路名/街道",
            "detail": "地址",
        }
        widgets = {
            "recipient_name": TextInput(),
            "is_default": CheckboxInput(),
            "phone": NumberInput(),
            "postal_code": NumberInput(),
            "county": TextInput(),
            "district": TextInput(),
            "road": TextInput(),
            "detail": TextInput(),
        }


UserAddressFormSet = modelformset_factory(
    UserAddress,
    form=UserAddressForm,
    extra=0,  # 不要額外的空表單
    can_delete=True,  # 如果需要刪除功能
)
