from django.shortcuts import render, redirect, get_object_or_404
from .models import Group, JoinedGroup
from .forms import GroupForm, ProductFormSet, ProductForm
from products.models import Product
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .services.exceptions import *
from .services.group_services import GroupService
from django.utils import timezone
from datetime import timedelta
from django.core.files.storage import default_storage
from django.http import JsonResponse
import os
import uuid
from django.core.paginator import Paginator
from django.urls import reverse
from django.http import HttpResponse
from django.conf import settings
import json

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
				group.save()	
				group.start_group()
				group.save()	

				product_formset.instance = group
				product_formset.save()		
			messages.success(request, "團購已建立")
			return redirect("groups:index_filtered", filter_type="owned")
	
		if product_formset.non_form_errors():
			messages.error(request, product_formset.non_form_errors()[0])

	else:
		group_form = GroupForm(prefix="group")
		product_formset = ProductFormSet(prefix="product", queryset=Product.objects.none())
	
	one_week_later = timezone.now() + timedelta(days=7)
	limited_config = settings.TINYMCE_LIMITED_CONFIG
	limited_config_json = json.dumps(limited_config)
	context = {
			"group_form": group_form,
			"product_form": product_formset,
			"empty_form": product_formset.empty_form,
			"one_week_later": one_week_later,
          	"limited_config_json": limited_config_json,
			}
	return render(request, "groups/new.html", context)

def detail(request, id):
	group = get_object_or_404(Group.objects.select_related("owner"), pk=id)
	user = request.user
	role = "guest"
	
	if request.method == "POST" and request.POST.get("_method") == "delete":
		if request.POST.get("role") == "owner":
			group.delete()
			messages.success(request, "團購已刪除")
			return redirect('groups:index_filtered', filter_type="owned")
		else:
			GroupService.leave_group(user=user, group=group)
			return redirect('groups:index_filtered', filter_type="followed")

	if user.is_authenticated and request.method == "POST":
		products_data = GroupService.prepare_products_data(request.POST)
		GroupService.join_group(user=user, group=group, products_data=products_data)
		role = "joiner"
	
	if user.is_authenticated:
		if group.owner == user:
			role = "owner"
		elif JoinedGroup.objects.filter(group=group, buyer=user).exists():
			role = "joiner"
	return render(request, "groups/detail.html", {"group": group, "role": role})

@login_required
def manage_edit(request, id):
	group = get_object_or_404(Group, id=id)
	if request.method == "POST" and request.user == group.owner:
		group_form = GroupForm(instance=group, prefix='group')
		product_formset = ProductFormSet(request.POST, request.FILES, queryset=Product.objects.filter(group=group), prefix="product")

		if group_form.is_valid() and product_formset.is_valid():
			with transaction.atomic():
					group_form.save()
					product_formset.save()
					messages.success(request, "團購已更新")
			return redirect("groups:detail", id=id)
		else:
			messages.warning(request, "欄位填寫有誤，請檢查後再試")
			return redirect("groups:manage_edit", id=id)

	else:
		group_form = GroupForm(instance=group, prefix="group")
		product_formset = ProductFormSet(queryset=Product.objects.filter(group=group), prefix="product")
	
	return render(request, "groups/manage_edit.html", {'group_form': group_form, 'product_formset': product_formset})

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


