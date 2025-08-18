from django.contrib import admin
from .models import Group, JoinedGroup

admin.site.register(Group)
admin.site.register(JoinedGroup)
