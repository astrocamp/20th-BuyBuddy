from django.forms import ModelForm
from .models import Group
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
        'min': 0,
        'step': '1',
        'required': True,
        'x-model': 'min_goal',
        'x-on:input': 'removeZero()'
      }),
      'deadline': DateInput(attrs={
        'class': 'w-full border-2 border-gray-300 rounded-md p-2', 
        'placeholder': '團購截止日期',
        'type': 'date',
        'required': True
      }),
    }