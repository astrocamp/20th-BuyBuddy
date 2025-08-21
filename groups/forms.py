from django.forms import DateField, ModelForm
from .models import Group
from django.forms.widgets import *

class GroupForm(ModelForm):
  class Meta:
    model = Group
    fields = ['name', 'banner', 'description', 'deadline', 'min_amount', 'min_quantity']