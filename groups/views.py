
from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from PIL import Image
import io, os
from .models import Group
from .forms import GroupForm
from datetime import datetime
from django.contrib.auth.decorators import login_required


def index(request):
  return render(request, "groups/index.html")


@login_required
def create_group(request):
  forms = GroupForm()
  if request.method == 'POST' and request.FILES.get('image'):

    form = GroupForm(request.POST, request.FILES)
    if form.is_valid():
      form_data = form.cleaned_data
      form_data.update({
        'owner': request.user,
        'status': '進行中',
        'created_at': datetime.now(),
        'deleted_at': None,
      })

      Group.objects.create(**form_data)
      return redirect('groups:create_group')
    else:
      return redirect('groups:create_group')
    
  return render(request, "groups/create_group.html", {"forms": forms})

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
