import json
import re
from pathlib import Path

from allauth.account.forms import ResetPasswordForm, ResetPasswordKeyForm

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import (
    get_default_password_validators,
    MinimumLengthValidator,
)
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.forms import (
    ModelForm,
    FileInput,
    TextInput,
    CheckboxInput,
    modelformset_factory,
)

from .models import User, UserAddress

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
            "password_mismatch": "兩次輸入的密碼不一致",
        }


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


class MyResetPasswordForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 這裡的 'email' 就是該頁面的必填欄位
        self.fields["email"].error_messages.update(
            {
                "required": "此欄位為必填",
                "invalid": "請輸入有效的電子郵件地址",
            }
        )


class CustomResetPasswordFromKeyForm(ResetPasswordKeyForm):
    error_messages = {
        "password_mismatch": "兩次輸入的密碼不一致，請再確認",
    }
    length_template = "密碼需要 {min_len} 個字符"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("password1", "password2"):
            f = self.fields[name]
            f.label = "新密碼" if name == "password1" else "再次輸入新密碼"
            f.error_messages["required"] = "此欄位為必填"
            f.validators.clear()
            f.help_text = ""
            f.min_length = None

    def clean_password1(self):
        return self.cleaned_data.get("password1")

    def clean_password2(self):
        return self.cleaned_data.get("password2")

    def clean(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")

        # 任一欄沒填 -> 交給 required 中文
        if not p1 or not p2:
            return self.cleaned_data

        # 先清掉可能殘留的欄位錯誤
        if hasattr(self, "_errors"):
            self._errors.pop("password1", None)
            self._errors.pop("password2", None)

        # 兩次不同 -> 兩欄都掛中文
        if p1 != p2:
            msg = self.error_messages["password_mismatch"]
            self.add_error("password1", msg)
            self.add_error("password2", msg)
            return self.cleaned_data

        # 長度不足 -> 兩欄都掛中文
        min_len = self._get_min_length()
        if len(p2) < min_len:
            msg = self.length_template.format(min_len=min_len)
            self.add_error("password1", msg)
            self.add_error("password2", msg)

        return self.cleaned_data

    # 核心：攔截任何被加上的錯誤，換成我們要的中文，且兩欄都顯示
    def add_error(self, field, error):
        # 只處理密碼兩欄
        if field in ("password1", "password2"):
            # 1) 帶 code 的錯誤（例如密碼太短）
            if isinstance(error, ValidationError):
                codes = {getattr(e, "code", None) for e in error.error_list}
                # 攔截「密碼太短」
                if "password_too_short" in codes:
                    msg = self.length_template.format(min_len=self._get_min_length())
                    super().add_error("password1", msg)
                    super().add_error("password2", msg)
                    return
                # 處理其他密碼強度相關的錯誤並提供中文訊息
                if "password_too_common" in codes:
                    msg = "您的密碼太過常見。"
                elif "password_entirely_numeric" in codes:
                    msg = "您的密碼不能全部是數字。"
                elif "password_too_similar" in codes:
                    msg = "您的密碼與您的個人資訊太過相似。"
                else:
                    # 對於未明確處理的驗證碼，保留原始錯誤，避免安全漏洞
                    super().add_error(field, error)
                    return

                super().add_error("password1", msg)
                super().add_error("password2", msg)
                return
            # 有些版本會用字串訊息；一併攔掉（直角與彎引號都處理）
            if isinstance(error, str):
                if (
                    "same password each time" in error
                    or "didn't match" in error
                    or "didn’t match" in error
                ):
                    msg = self.error_messages["password_mismatch"]
                    super().add_error("password1", msg)
                    super().add_error("password2", msg)
                    return

        # 其他情況維持原行為（例如 required）
        return super().add_error(field, error)

    def _get_min_length(self) -> int:
        # 讀取 settings.AUTH_PASSWORD_VALIDATORS 的長度設定；找不到就用 8
        for v in get_default_password_validators():
            if isinstance(v, MinimumLengthValidator):
                return getattr(v, "min_length", 8)
        return 8
