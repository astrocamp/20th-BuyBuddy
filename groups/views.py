from django.shortcuts import render, redirect
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
      # group_form.save()
      print(data.min_goal)
      messages.info(request, "團購已建立")
      return redirect('groups:index')
    else:
      print(group_form.errors)
      messages.warning(request, "出現錯誤稍候再試")
      return redirect('groups:create_group')
  group_form = GroupForm()
  return render(request, 'groups/create_group.html', {'group_form': group_form})

def upload_img(request):
    return render(request, "groups/upload_img.html")

def create_img(request):
  if request.method == 'POST' and request.FILES.get('image'):
    img = Image.open(request.FILES['image'])
    img_name = os.path.splitext(request.FILES['image'].name)[0]
    
    if img.mode in ['RGBA', 'P']:
      img = img.convert('RGB')
    
    img_io = io.BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)

    img_file = ContentFile(
      img_io.getvalue(),
      name=f"processed_{img_name}.jpg"
    )

    Group.objects.create(banner=img_file)
    print('儲存:', Group.objects.all())
    
    return redirect('groups:read_img')
  
  return render(request, 'groups/upload_img.html')
  
def read_img(request):
  photos = Group.objects.all()
  return render(request, 'groups/upload_img.html', {"photos": photos})

