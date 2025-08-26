from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.base import ContentFile
from PIL import Image
import io, os
from .models import Group
from .forms import GroupForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def index(request):
  return render(request, "groups/index.html")


@login_required
def create_group(request):
  if request.method == 'POST':
    group_form = GroupForm(request.POST, request.FILES)
    if group_form.is_valid():
      data = group_form.save(commit=False)
      data.owner = request.user
      data.status = '進行中'
      group_form.save()
      messages.success(request, "團購已建立")
      return redirect('groups:index')
    else:
      print(group_form.errors)
      messages.warning(request, "欄位填寫有誤，請檢查後再試")
      return redirect('groups:create_group')
  group_form = GroupForm()
  return render(request, 'groups/create_group.html', {'group_form': group_form})

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


