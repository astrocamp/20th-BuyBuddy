from django.forms import (
    ModelForm,
    FileInput,
    TextInput,
    CheckboxInput,
    modelformset_factory,
)
from .models import User, UserAddress
from django import forms
from django.conf import settings
from pathlib import Path
import json
import re

# 讀出縣市區域的
_DATA_PATH = Path(settings.BASE_DIR) / "public" / "assets" / "taiwan-districts.json"
with _DATA_PATH.open(encoding="utf-8") as f:
    _RAW = json.load(f)

# 把縣市 json 轉成 dict 格式
_DATA_MAP = {}
for item in _RAW:
    county = item["name"]
    districts = []
    for d in item["districts"]:
        districts.append({"district": d["name"], "zip": d["zip"]})

    _DATA_MAP[county] = districts

# 把縣市＋區域的郵遞區號組合，以便對照
_VALID = {}
for county, districts in _DATA_MAP.items():
    for d in districts:
        _VALID[(county, d["district"])] = d["zip"]


class RegistrationForm(ModelForm):
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput,
        error_messages={
            "required": "請輸入密碼",
            "min_length": "密碼至少需要 8 個字符",
        },
    )

    class Meta:
        model = User
        fields = ["username", "email", "password"]
        error_messages = {
            "username": {
                "required": "請輸入用戶名",
            },
            "email": {
                "required": "請輸入電子郵件地址",
                "invalid": "請輸入有效的電子郵件地址",
            },
        }

    def clean_email(self):
        # 檢查 email 是否已存在
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("此 Email 已被註冊，請使用其他信箱")
        return email

    def clean_username(self):
        # 檢查 username 是否重複
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("此用戶名已被使用，請選擇其他用戶名")
        return username


class LoginForm(forms.Form):
    email = forms.EmailField(
        error_messages={
            "required": "請輸入電子郵件地址",
            "invalid": "請輸入有效的電子郵件地址",
        }
    )

    password = forms.CharField(
        error_messages={
            "required": "請輸入密碼",
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
    county = forms.ChoiceField(
        choices=(),
        required=True,
        label="城市/縣",
        error_messages={
            "required": "請選擇縣市",
            "invalid_choice": "請選擇有效的縣市",
        },
    )
    district = forms.ChoiceField(
        choices=(),
        required=True,
        label="區域",
        error_messages={
            "required": "請選擇區域",
            "invalid_choice": "請選擇有效的區域",
        },
    )

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
        error_messages = {
            "recipient_name": {"required": "請輸入收件人姓名"},
            "phone": {
                "required": "請輸入手機號碼",
                "invalid": "請輸入有效的手機號碼",
            },
            "postal_code": {"required": "請先選擇縣市與區域，系統會自動帶入郵遞區號"},
            "road": {"required": "請輸入路名/街道"},
            "detail": {"required": "請輸入地址"},
        }
        labels = {
            "recipient_name": "收件人姓名",
            "is_default": "設爲預設",
            "phone": "收件人手機",
            "postal_code": "郵遞區號",
            "road": "路名/街道",
            "detail": "地址",
        }
        widgets = {
            "recipient_name": TextInput(),
            "is_default": CheckboxInput(),
            "phone": TextInput(
                attrs={
                    "inputmode": "numeric",
                    "pattern": r"09\d{8}",
                    "placeholder": "09xxxxxxxx",
                }
            ),
            "postal_code": TextInput(
                attrs={
                    "inputmode": "numeric",
                    "readonly": "readonly",
                }
            ),
            "county": forms.Select(attrs={}),
            "district": forms.Select(),
            "road": TextInput(),
            "detail": TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        county_choices = [("", "請選擇縣市")] + [(c, c) for c in _DATA_MAP.keys()]
        self.fields["county"].choices = county_choices

        current_county = (
            self.data.get("county")
            or self.initial.get("county")
            or getattr(self.instance, "county", "")
        )

        if current_county in _DATA_MAP:
            districts_choices = [("", "請選擇區域")] + [
                (d["district"], d["district"]) for d in _DATA_MAP[current_county]
            ]
        else:
            districts_choices = [("", "請先選擇縣市")]

        self.fields["district"].choices = districts_choices

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not re.fullmatch(r"09\d{8}", phone):
            raise forms.ValidationError("手機格式錯誤")
        return phone

    # 驗證縣市的郵遞區號
    # 不正確就直接覆寫
    def clean(self):
        cleaned_data = super().clean()
        county = (cleaned_data.get("county") or "").strip()
        district = (cleaned_data.get("district") or "").strip()

        if county and district:
            valid_zip = _VALID.get((county, district))
            if valid_zip:
                cleaned_data["postal_code"] = valid_zip
            else:
                self.add_error("district", "該區不屬於所選縣市")

        return cleaned_data


UserAddressFormSet = modelformset_factory(
    UserAddress,
    form=UserAddressForm,
    extra=0,
)
