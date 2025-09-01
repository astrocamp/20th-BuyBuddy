from django.forms import (
    ModelForm,
    FileInput,
    TextInput,
    CheckboxInput,
    NumberInput,
)
from .models import User, UserAddress
from django import forms
from django.core.validators import MinLengthValidator


class RegistrationForm(ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 幫密碼加上最小長度驗證器
        self.fields["password"].validators.append(
            MinLengthValidator(8, message="密碼至少需要 8 個字符。")
        )

        self.fields["password"].min_length = 8

        # 自定義錯誤訊息
        self.fields["username"].error_messages = {
            "required": "請輸入用戶名。",
        }
        self.fields["email"].error_messages = {
            "required": "請輸入電子郵件地址。",
            "invalid": "請輸入有效的電子郵件地址。",
        }
        self.fields["password"].error_messages = {
            "required": "請輸入密碼。",
        }

    def clean_email(self):
        # 檢查 email 是否已存在
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("此 Email 已被註冊，請使用其他信箱。")
        return email

    def clean_username(self):
        # 檢查 username 是否已存在
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("此用戶名已被使用，請選擇其他用戶名。")
        return username


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
            "avatar_url": FileInput(attrs={"@change": "handleFile($event)", "accept": "image/*"}),
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
            "county": "縣市",
            "district": "鄉鎮市區",
            "road": "住址1",
            "detail": "住址2",
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
