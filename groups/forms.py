from django.forms import ModelForm
from django import forms
from .models import Group
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

