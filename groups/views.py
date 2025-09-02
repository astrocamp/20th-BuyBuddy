from django.shortcuts import render, redirect, get_object_or_404
from .models import Group, JoinedGroup
from .forms import GroupForm, ProductFormSet
from products.models import Product
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .services.exceptions import *
from .services.group_services import GroupService
from django.utils import timezone
from datetime import datetime
from django.core.files.storage import default_storage
from django.http import JsonResponse
import os
import uuid
from django.core.paginator import Paginator
from django.urls import reverse
from django.http import HttpResponse


def index(request, filter_type="ongoing"):
	user = request.user

	protected_filters = ["owned", "followed"]

	if filter_type in protected_filters and not user.is_authenticated:
		login_url = reverse("users:sessions_new")
		next_url = request.path

		if request.headers.get("HX-Request") == "true":
			response = HttpResponse()
			response["HX-Redirect"] = f"{login_url}?next={next_url}"
			return response
		else:
			return redirect(f"{login_url}?next={next_url}")

	status_filter = request.GET.get("status", "ongoing")

	if filter_type == "owned" and user.is_authenticated:
		all_groups = Group.objects.filter(owner=user)
		if status_filter in ["ongoing", "reached"]:
			all_groups = all_groups.filter(status=status_filter)
	elif filter_type == "followed" and user.is_authenticated:
		all_groups = Group.objects.filter(joinedgroup__buyer=user)
		if status_filter in ["ongoing", "reached"]:
			all_groups = all_groups.filter(status=status_filter)
	else:
		filter_type = "ongoing"
		all_groups = Group.objects.filter(status="ongoing")
		status_filter = None

	all_groups = all_groups.order_by("-id")

	paginator = Paginator(all_groups, 3)
	page_number = request.GET.get("page")
	page_groups = paginator.get_page(page_number)

	context = {
		"page_groups": page_groups,
		"active_tab": filter_type,
		"active_status": status_filter,
	}

	if request.headers.get("HX-Request") == "true":
		return render(request, "groups/shared/htmx_response.html", context)
	else:
		return render(request, "groups/index.html", context)


@login_required
def new(request):
	if request.method == "POST":
		group_form = GroupForm(request.POST, request.FILES, prefix="group")
		product_formset = ProductFormSet(request.POST, request.FILES, prefix="product")
		if group_form.is_valid() and product_formset.is_valid():
			with transaction.atomic():
				group = group_form.save(commit=False)
				group.owner = request.user
				group.status = "ongoing"
				group.save()	

				product_formset.instance = group
				product_formset.save()		
			messages.success(request, "團購已建立")
			return redirect("groups:owned")
		else:
			messages.warning(request, "欄位填寫有誤，請檢查後再試")
			context = {
				"group_form": group_form,
				"product_form": product_formset,
				"empty_form": product_formset.empty_form,
			}
			return render(request, "groups/new.html", context)
			
	else:
		group_form = GroupForm(prefix="group")
		product_formset = ProductFormSet(prefix="product", queryset=Product.objects.none())
		context = {
			"product_form": product_formset, 
			"group_form": group_form,
			"empty_form": product_formset.empty_form
			}
		return render(request, "groups/new.html", context)

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
			return render(request, "groups/detail.html", {"group": group})

	if request.user.is_authenticated and request.method == "POST":
		user = request.user
		products_data = GroupService.prepare_products_data(request.POST)
		GroupService.join_group(user=user, group=group, products_data=products_data)
		return redirect("groups:detail", id=id)

	return render(request, "groups/detail.html", {"group": group})


def update_quantity(request, id):
	group = get_object_or_404(Group, pk=id)
	return render(request, "groups/member_edit.html", {"group": group})


@login_required
def manage(request, id):
	group = get_object_or_404(Group, pk=id)
	if request.method == "POST":
		if request.POST.get("_method") == "delete":
			group_id = request.POST.get("group-id")
			group = get_object_or_404(Group, pk=group_id)
			if group.owner != request.user:
				messages.warning(request, "您無權刪除此團購")
				return redirect('groups:manage')
			group.delete()
			messages.success(request, "團購已刪除")
			return redirect('groups:index_filtered', filter_type="owned")
	return render(request, "groups/manage.html", {"group": group})


@login_required
def manage_edit(request, id):
	group = get_object_or_404(Group, id=id)
	product = get_object_or_404(Product, group=group)
	group_form = GroupForm(instance=group, prefix='group')
	product_form = ProductForm(instance=product, prefix='product')
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

@login_required
def upload_image(request):
	if request.method == "POST" and request.FILES:
		try:
			upload_file = request.FILES['file']
			file_extension = os.path.splitext(upload_file.name)[1].lower()
			file_name = f"{uuid.uuid4()}{file_extension}"

			s3_path = f"groups/detail/{file_name}"
			path = default_storage.save(s3_path, upload_file)
			file_url = default_storage.url(path)
			return JsonResponse({"location": file_url})
		
		except Exception as e:
			return JsonResponse({"error": "上傳失敗，請稍後再試"}, status=500)
	return JsonResponse({"error": "無效請求"}, status=400)


