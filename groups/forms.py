from django.forms import DateField, ModelForm
from .models import Group
from django.forms.widgets import *

class GroupForm(ModelForm):
  class Meta:
    model = Group
    fields = ['name', 'banner', 'description', 'deadline', 'min_amount', 'min_quantity']
    widgets = {
      'name': TextInput(attrs={
        'class': 'w-1/2 border-2 border-gray-300 rounded-md p-2', 
        'placeholder': '團購名稱'}),
      'banner': FileInput(attrs={
        'class': 'w-1/2 border-2 border-gray-300 rounded-md p-2', 
        'placeholder': '團購圖片'}),
      'description': Textarea(attrs={
        'class': 'w-1/2 border-2 border-gray-300 rounded-md p-2 resize-y', 
        'placeholder': '團購描述'}),
      'min_amount': NumberInput(attrs={
        'id': 'min_amount_num', 'class': 'w-full border-2 border-gray-300 rounded-md p-2', 
        'placeholder': '成團金額', 'type': 'number'}),
      'min_quantity': NumberInput(attrs={
        'id': 'min_quantity_num', 
        'class': 'w-full border-2 border-gray-300 rounded-md p-2', 
        'placeholder': '成團數量', 'step': 1}),
      'deadline': DateInput(
        attrs={
          'class': 'w-1/2 border-2 border-gray-300 rounded-md p-2', 
          'placeholder': '團購截止日期', 'type': 'date'}),
    }