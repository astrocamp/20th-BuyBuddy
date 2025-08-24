from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from groups.models import Group
from groups.forms import GroupForm
from products.models import Product
from .services import exceptions
from .services.group_services import GroupService

def index(request):
    groups = Group.objects.all().prefetch_related('products')
    group_formset = modelformset_factory(Group, form=GroupForm, extra=0)
    formset = group_formset(queryset=groups)
    user = request.user
    if request.method == "POST" and request.POST.get("_method") == "delete":
        group_id = request.POST["group-id"]
        group = Group.objects.get(pk=group_id)
        GroupService.leave_group(user=user, group=group)
        return redirect("buy:index")
    return render(request, "buy/index.html", {"formset": formset, "groups":groups})

@login_required
def purchase(request):
    if request.method == "POST":
        user = request.user
        group = Group.objects.get(pk=request.POST.get("group-id"))
        products_data = GroupService.prepare_products_data(request.POST)
        GroupService.join_group(user=user, group=group, products_data=products_data)
    return redirect("buy:index")



        