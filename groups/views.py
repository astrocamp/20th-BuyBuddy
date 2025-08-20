
from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from PIL import Image
import io, os
from .models import Group
from .forms import GroupForm
from datetime import datetime

def index(request):
  return render(request, "groups/index.html")

def create_group(request):
  forms = GroupForm()
  if request.method == 'POST':
    name = request.POST.get('name')
    min_amount = request.POST.get('min_amount')
    min_quantity = request.POST.get('min_quantity')
    goal_choice = request.POST.get('goal_choice')
    banner = request.FILES.get('banner')
    description = request.POST.get('description')
    deadline = request.POST.get('deadline')
    status = '進行中'
    created_at = datetime.now()
    deleted_at = None


    print('name:', name);
    print('min_amount:', min_amount);
    print('min_quantity:', min_quantity);
    print('goal_choice:', goal_choice);
    print('banner:', banner);
    print('description:', description);
    print('deadline:', deadline);
    print('status:', status);
    print('created_at:', created_at);
    print('deleted_at:', deleted_at);

    
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
