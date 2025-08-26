from django.shortcuts import render, redirect, get_object_or_404
from .models import Group
from .forms import GroupForm, ProductForm , ProductImageForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

def index(request):
  return render(request, "groups/index.html")

def render_form(request):
  product_form = ProductForm()
  group_form = GroupForm()
  productImage_form = ProductImageForm()
  return render(request, 'groups/render_form.html', {'product_form': product_form, 'group_form': group_form, 'productImage_form': productImage_form})

@login_required
def create_group(request):
  if request.method == 'POST':
    group_form = GroupForm(request.POST, request.FILES)
    product_form = ProductForm(request.POST)
    productImage_form = ProductImageForm(request.POST, request.FILES)
    if group_form.is_valid() and product_form.is_valid() and productImage_form.is_valid():
      with transaction.atomic():
        group = group_form.save(commit=False)
        group.owner = request.user
        group.status = '進行中'
        group.save()
        product = product_form.save(commit=False)
        product.group = group
        product.save()
        productImage = productImage_form.save(commit=False)
        productImage.order = 1
        productImage.product = product
        productImage.save()
        messages.success(request, "團購已建立")
        return redirect('groups:read_group')
    else:
      messages.warning(request, "欄位填寫有誤，請檢查後再試")
      return redirect('groups:render_form')
  return redirect('groups:render_form')

@login_required
def read_group(request):
  groups = Group.objects.all()
  return render(request, 'groups/read_group.html', {'groups': groups})

@login_required
def edit_group(request, id):
  group = get_object_or_404(Group, id=id)
  
  if request.method == 'POST':
    if request.user == group.owner:
      group_form = GroupForm(request.POST, request.FILES, instance=group)
      if group_form.is_valid():
        group_form.save()
        messages.success(request, "團購已更新")
        return redirect('groups:read_group')
      else:
        print(group_form.errors)
        messages.warning(request, "欄位填寫有誤，請檢查後再試")
        return redirect('groups:edit_group', id=id)
    else:
      messages.warning(request, "您無權編輯此團購")
      return redirect('groups:read_group')


  group_form = GroupForm(instance=group)
  exclude_fields = ['deadline', 'min_goal']
  for field_name, field in group_form.fields.items():
    if field_name not in exclude_fields:
      field.widget.attrs.update({
        'class': 'w-full border-2 border-gray-300 rounded-md p-2 cursor-not-allowed',
        'readonly': 'readonly',
      })
  
  return render(request, 'groups/edit_group.html', {'group_form': group_form, 'group': group})

@login_required
def delete_group(request, id):
  group = get_object_or_404(Group, id=id)
  if request.method == 'POST':
    if request.user == group.owner:
      group.delete()
      messages.success(request, "團購已刪除")
      return redirect('groups:read_group')
    else:
      messages.warning(request, "您無權刪除此團購")
      return redirect('groups:read_group')
  return redirect('groups:read_group')


