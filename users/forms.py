from django.forms import ModelForm, FileInput, TextInput, PasswordInput, CheckboxInput, NumberInput
from .models import User, UserAddress

class UserForm(ModelForm):
    class Meta:
        model = User
        fields = [ "avatar_url", "username", "password"]
        labels = {
            "avatar_url": "大頭照",
            "username": "用戶名稱",
            "password": "密碼"
        }
        widgets = {
            "avatar_url": FileInput(),
            "username": TextInput(),
            "password": PasswordInput(),
        }

class UserAddressForm(ModelForm):
    class Meta:
        model = UserAddress
        fields = [ "recipient_name", "is_default", "phone", "postal_code", "county", "district", "road", "detail" ]
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


