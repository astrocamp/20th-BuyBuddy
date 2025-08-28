from django.shortcuts import render, redirect, get_object_or_404
from .models import Group
from products.models import ProductImage
from .forms import GroupForm, ProductFormSet, ProductImageForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

def index(request):
  return render(request, "groups/index.html")

def render_form(request):
  group_form = GroupForm()
  product_form = ProductFormSet()
  image_form = ProductImageForm()
  return render(request, 'groups/render_form.html', {'product_form': product_form, 'group_form': group_form, 'image_form': image_form})

@login_required
def create_group(request):
  if request.method == 'POST':
    group_form = GroupForm(request.POST, request.FILES)
    if group_form.is_valid():
      with transaction.atomic():
        group = group_form.save(commit=False)
        group.owner = request.user
        group.status = '進行中'
        group.save()
        product_formset = ProductFormSet(request.POST, instance=group)
        if product_formset.is_valid():
            products = product_formset.save(commit=False)
            for i, product in enumerate(products):
              product.save()
              images = request.FILES.getlist(f'url_{i}')
              for j, image in enumerate(images):
                ProductImage.objects.create(
                    product=product,
                    url=image,
                    order=j
                )
            messages.success(request, "團購已新增")
            return redirect('groups:render_form')
    else:
        messages.warning(request, "欄位填寫有誤，請檢查後再試")
        group_form = GroupForm()
        product_formset = ProductFormSet()
        return render(request, 'groups/render_form.html', {'product_form': product_formset, 'group_form': group_form})
  return redirect('groups:render_form')

@login_required
def read_group(request):
  owner = request.user
  groups = Group.objects.filter(owner=owner)
  return render(request, 'groups/read_group.html', {'groups': groups})

@login_required
def edit_group(request, id):
  group = get_object_or_404(Group, id=id)
  if request.user != group.owner:
    messages.warning(request, "您無權編輯此團購")
    return redirect('groups:read_group')

  group_form = GroupForm(instance=group)
  product_form = ProductFormSet(instance=group)
  
  if request.method == 'POST':
    group_form = GroupForm(request.POST, request.FILES, instance=group)
    if group_form.is_valid():
      with transaction.atomic():
        group_form.save()
        product_formset = ProductFormSet(request.POST, instance=group)
        if product_formset.is_valid():
          product_formset.save()
          products = product_formset.save(commit=False)
          for i, product in enumerate(products):
            for old_image in product.images.all():
              old_image.url.delete()
              old_image.delete()
            new_images = request.FILES.getlist(f'url_{i}')
            for j, image in enumerate(new_images):
              ProductImage.objects.create(
                product=product,
                url=image,
                order=j
              )
          messages.success(request, "團購已更新")
          return redirect('groups:render_form')
        else:
          messages.warning(request, "欄位填寫有誤，請檢查後再試")
          group_form = GroupForm()
          product_formset = ProductFormSet()
          return redirect('groups:edit_group', id=id)

  return render(request, 'groups/edit_group.html', {'product_form': product_form, 'group_form': group_form, })

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


