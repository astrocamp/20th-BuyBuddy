from django.forms import ModelForm, inlineformset_factory, BaseInlineFormSet
from django import forms
from .models import Group
from products.models import Product
from django.forms.widgets import *
from tinymce.widgets import TinyMCE
from django.conf import settings
from django.utils.timezone import now


class GroupForm(ModelForm):
    goal_choice = forms.ChoiceField(
        choices=Group.GOAL_CHOICES,
        label='成團方式',
        required=True,
        widget=forms.Select(
            attrs={"class": "w-full border-2 border-tertiary-color-300 rounded-lg p-2"}
        ),
        error_messages={"required": "請選擇成團標準"},
    )

    class Meta:
        model = Group
        fields = [
            "name",
            "banner",
            "description",
            "deadline",
            "goal_choice",
            "min_goal",
        ]
        labels = {
            "name": "團購名稱",
            "banner": "團購圖片",
            "description": "團購描述",
            "deadline": "團購截止日期",
            "goal_choice": "成團方式",
            "min_goal": "成團目標",
        }
        error_messages = {
            "name": {
                "required": "請輸入團購名稱",
            },
            "banner": {
                "required": "請選擇團購圖片",
            },
            "description": {
                "required": "請輸入團購介紹",
            },
            "deadline": {
                "required": "請輸入截止日期",
            },
            "min_goal": {
                "required": "請輸入成團金額/數量",
            },
        }
        
    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline.date() < now().date():
            raise forms.ValidationError("截止日期不能早於今天")
        return deadline
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["deadline"].widget.attrs["min"] = now().strftime("%Y-%m-%d")
            


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "price", "description", "banner"]
        labels = {
            "name": "產品名稱",
            "price": "產品價格",
            "description": "產品描述",
            "banner": "產品圖片",
        }
        error_messages = {
            "name": {
                "required": "請輸入商品名稱",
            },
            "price": {
                "required": "請輸入商品單價",
            },
            "description": {
                "required": "請輸入商品介紹",
            },
            "banner": {
                "required": "請上傳商品圖片",
            },
        }
        widgets = {
            "description": TinyMCE(mce_attrs=settings.TINYMCE_LIMITED_CONFIG),
        }


class ProductBaseForm(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        if instance and instance.pk:
            self.extra = 0

    def clean(self):
        super().clean()

        valid_forms = 0

        for form in self.forms:
            has_data = any(
                [
                    form.cleaned_data.get("name"),
                    form.cleaned_data.get("price"),
                    form.cleaned_data.get("description"),
                    form.cleaned_data.get("banner"),
                ]
            )

            if has_data:
                if all(
                    [
                        form.cleaned_data.get('name'),
                        form.cleaned_data.get('price'),
                        form.cleaned_data.get('description'),
                    ]
                ):
                    valid_forms += 1

        if valid_forms == 0:
            raise forms.ValidationError('請至少添加一個完整的產品')


ProductFormSet = inlineformset_factory(
	Group,
	Product,
	form=ProductForm,
	fields=['name', 'price', 'description', "banner"],
	extra=2,
	can_delete=False,
	labels = {
		'name': '產品名稱',
		'price': '產品價格',
		'description': '產品描述',
		'banner': '產品圖片'
		},
	formset = ProductBaseForm) 

class URLExtractForm(forms.Form):
	url = forms.URLField(
		label="產品網址",
		required=True,
		widget=forms.URLInput(),
		error_messages={
			"required": "請輸入有效網址",
			"invalid": "請輸入有效網址"
		}
	)
					

 




