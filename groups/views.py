from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from PIL import Image
import io, os
from .models import Group

def index(request):
    return render(request, "index.html")

def upload(request):
    return render(request, "groups/upload.html")

def create(request):
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
    
    return redirect('groups:read')
  return render(request, 'groups/upload.html')
  
def read(request):
  photos = Group.objects.all()
  return render(request, 'groups/upload.html', {"photos": photos})
