from django.forms import ModelForm
from .models import Product
from django.forms.widgets import TextInput, NumberInput, Textarea


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
            'class': 'w-full border-2 border-gray-300 rounded-md p-2',
            'placeholder': '產品名稱',
            'required': True
        }),
        'price': NumberInput(attrs={
            'class': 'w-full border-2 border-gray-300 rounded-md p-2',
            'placeholder': '產品價格',
            'required': True
        }),
        'description': Textarea(attrs={
            'class': 'w-full border-2 border-gray-300 rounded-md p-2 resize-y',
            'placeholder': '產品描述',
            'rows': 5,
            'required': True
        })
    }