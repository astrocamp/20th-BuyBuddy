from django.forms import ModelForm, inlineformset_factory, BaseInlineFormSet
from .models import Product
from groups.models import Group
from django.forms.widgets import *

class ProductForm(ModelForm):
	class Meta:
		model = Product
		fields = ['name', 'price', 'description', 'image']
		
class ProductBaseFormSet(BaseInlineFormSet):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		instance = kwargs.get('instance', None)
		if instance and instance.pk:
			self.extra = 0
		elif self.is_bound:
			self.extra = 0
		else:
			self.extra = 2
	   

ProductFormSet = inlineformset_factory(
	Group,
	Product,
	form=ProductForm,              
	formset=ProductBaseFormSet,
	fields=['name', 'price', 'description', 'image'],
	can_delete=True,
	validate_min=True,
	min_num=0,
	labels = {
	  'name': '產品名稱',
	  'price': '產品價格',
	  'description': '產品描述'
	}
)