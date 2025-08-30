from django.forms import ModelForm, inlineformset_factory, BaseInlineFormSet
from django import forms
from .models import Group
from products.models import Product
from django.forms.widgets import *


class GroupForm(ModelForm):
  goal_choice = forms.ChoiceField(
    choices=[
          ('1', '金額'),
          ('2', '數量')
      ],
      label='成團方式'
  )
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

class ProductForm(BaseInlineFormSet):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    instance = kwargs.get('instance', None)
    if instance and instance.pk:
      self.extra = 0

ProductFormSet = inlineformset_factory(
    Group,
    Product,
    fields=['name', 'price', 'description'],
    extra=2,
    can_delete=False,
    labels = {
      'name': '產品名稱',
      'price': '產品價格',
      'description': '產品描述'
    },
    formset = ProductForm
)
