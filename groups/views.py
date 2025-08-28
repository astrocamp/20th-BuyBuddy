from django.shortcuts import render, redirect, get_object_or_404
from .models import Group, JoinedGroup
from products.models import Product, ProductImage
from .forms import GroupForm, ProductForm , ProductImageForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .services.exceptions import *
from .services.group_services import GroupService

def index(request):
	groups = Group.objects.filter(status="ongoing")
	return render(request, "groups/index.html", {"groups": groups})

def new(request):
	product_form = ProductForm()
	group_form = GroupForm()
	productImage_form = ProductImageForm()
	return render(request, 'groups/new.html', {'product_form': product_form, 'group_form': group_form, 'productImage_form': productImage_form})

@login_required
def owned(request):
	groups = Group.objects.filter(owner=request.user)
	if request.method == 'POST':
		if request.POST.get("_method") == "delete":
			group_id = request.POST.get("group-id")
			group = get_object_or_404(Group, pk=group_id)
			if group.owner != request.user:
				messages.warning(request, "您無權刪除此團購")
				return redirect('groups:owned')
			group.delete()
			messages.success(request, "團購已刪除")
			return redirect('groups:owned')

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
			return redirect("groups:owned")
		else:
			messages.warning(request, "欄位填寫有誤，請檢查後再試")
		return redirect("groups:new")	
	return render(request, "groups/owned.html", {"groups": groups})

@login_required
def followed(request):
	groups = Group.objects.filter(
		joinedgroup__buyer=request.user,
		status__in=["ongoing", "reached"]
	)
	ongoing_groups = [ group for group in groups if group.status == "ongoing"]
	reached_groups = [ group for group in groups if group.status == "reached"]

	return render(request, "groups/followed.html", {"ongoing_groups": ongoing_groups, "reached_groups": reached_groups})

def detail(request, id):
	group = get_object_or_404(Group, pk=id)
	if request.user.is_authenticated:
		if group.owner == request.user:
			return redirect('groups:manage', id=id)
	
		try:
			joined_group = JoinedGroup.objects.get(
				group=group,
				buyer=request.user,
			)
			return redirect("groups:update_quantity", id=id)
		except JoinedGroup.DoesNotExist:
			pass

	if request.user.is_authenticated and request.method == "POST":
		user = request.user
		products_data = GroupService.prepare_products_data(request.POST)
		GroupService.join_group(user=user, group=group, products_data=products_data)
		return redirect("groups:detail", id=id)
	
	return render(request, "groups/detail.html", {"group": group})


def update_quantity(request, id):
	group = get_object_or_404(Group, pk=id)
	return render(request, "groups/member_edit.html", {"group": group})


def manage(request, id):
	group = get_object_or_404(Group, pk=id)
	return render(request, "groups/manage.html", {"group": group})

@login_required
def manage_edit(request, id):
	group = get_object_or_404(Group, id=id)
	product = get_object_or_404(Product, group=group)
	productImage = get_object_or_404(ProductImage, product=product)
	group_form = GroupForm(instance=group, prefix='group')
	product_form = ProductForm(instance=product, prefix='product')
	productImage_form = ProductImageForm(instance=productImage, prefix='product_image')
	if request.method == 'POST':
		if request.user == group.owner:
			group_form = GroupForm(request.POST, request.FILES, instance=group, prefix='group')
			product_form = ProductForm(request.POST, instance=product, prefix='product')
			productImage_form = ProductImageForm(request.POST, request.FILES, instance=productImage, prefix='product_image')
			if group_form.is_valid() and product_form.is_valid() and productImage_form.is_valid():
				with transaction.atomic():
					group = group_form.save()
					product = product_form.save()
					productImage = productImage_form.save()
					messages.success(request, "團購已更新")
				return redirect('groups:owned')
			else:
				messages.warning(request, "欄位填寫有誤，請檢查後再試")
				return redirect('groups:manage_edit', id=id)
		else:
			messages.warning(request, "您無權編輯此團購")
			return redirect('groups:manage_edit', id=id)
	return render(request, 'groups/manage_edit.html', {'group_form': group_form, 'group': group, 'product_form': product_form, 'productImage_form': productImage_form})
	


