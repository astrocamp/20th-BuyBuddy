from django.forms import ModelForm
from .models import Group
from products.models import Product, ProductImage
from django.forms.widgets import *


class GroupForm(ModelForm):
  class Meta:
    model = Group
    fields = ['name', 'banner', 'description', 'deadline', 'goal_choice', 'min_goal']
    labels = {
        'name': '團購名稱',
        'banner': '團購圖片',
        'description': '團購描述',
        'deadline': '團購截止日期',
        'goal_choice': '成團方式',
        'min_goal': '成團目標'
    }
    widgets = {
      'name': TextInput(attrs={
        'id': 'group_name',
        'class': 'w-full border-2 border-gray-300 rounded-md p-2', 
        'placeholder': '團購名稱',
        'required': True,
      }),
      'banner': FileInput(attrs={
        'class': 'w-full border-2 border-gray-300 rounded-md p-2', 
        'placeholder': '團購圖片',
        'required': True
      }),
      'description': Textarea(attrs={
        'id': 'group_description',
        'class': 'w-full border-2 border-gray-300 rounded-md p-2 resize-y', 
        'placeholder': '團購描述',
        'rows': 5,
        'required': True
      }),
      'goal_choice': Select(choices=[('amount', '金額'), ('quantity', '數量')], 
      attrs={
        'class': 'w-full border-2 border-gray-300 rounded-md p-2', 
        'required': True,
      }),
      'min_goal': NumberInput(attrs={
        'class': 'w-full border-2 border-gray-300 rounded-md p-2', 
        'placeholder': '成團數量',
        'min': 1,
        'required': True,
        'x-model': 'min_goal',
        'x-ref': 'min_goal',
        'x-on:input': 'removeZero()'
      }),
      'deadline': DateInput(attrs={
        'class': 'w-full border-2 border-gray-300 rounded-md p-2', 
        'placeholder': '團購截止日期',
        'type': 'date',
        'required': True
      }),
    }

class ProductForm(ModelForm):
  class Meta:
    model = Product
    fields = ['name', 'price', 'description']
    labels = {
      'name': '產品名稱',
      'price': '產品價格',
      'description': '產品描述'
    }
    widgets = {
      'name': TextInput(attrs={
        'id': 'product_name',
        'class': 'w-full border-2 border-gray-300 rounded-md p-2', 
        'placeholder': '產品名稱',
        'required': True,
      }),
      'price': NumberInput(attrs={
        'class': 'w-full border-2 border-gray-300 rounded-md p-2', 
        'placeholder': '產品價格',
        'required': True,
        'min': 1,
      }),
      'description': Textarea(attrs={
        'id': 'product_description',
        'class': 'w-full border-2 border-gray-300 rounded-md p-2 resize-y', 
        'placeholder': '產品描述',
        'rows': 5,
        'required': True,
      }),
    }
  def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 只有在編輯現有物件時才鎖定欄位
        if self.instance and self.instance.pk:
            exclude_fields = ['deadline', 'min_goal']
            for field_name, field in self.fields.items():
                if field_name not in exclude_fields:
                    field.widget.attrs['readonly'] = True
                    field.widget.attrs['class'] += ' cursor-not-allowed'  


class ProductImageForm(ModelForm):
  class Meta:
    model = ProductImage
    fields = ['url']
    labels = {
      'url': '圖片'
    }
    widgets = {
      'url': FileInput(attrs={
        'class': 'w-full border-2 border-gray-300 rounded-md p-2', 
        'placeholder': '圖片',
        'required': True,
      }),
    }
  