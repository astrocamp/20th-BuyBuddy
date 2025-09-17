from django.shortcuts import render, redirect, get_object_or_404
from .models import Group, JoinedGroup
from products.models import JoinedGroupProduct
from orders.models import Order
from .forms import GroupForm, ProductFormSet, ProductForm, URLExtractForm
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
from django.db.models import F, Subquery, OuterRef
from django.db.models.functions import Coalesce
from .services.scraper_service import  scrape_product_url_sync
import itertools
from django.forms import formset_factory
import requests
from django.core.files.base import ContentFile
import re
from django.utils.datastructures import MultiValueDict

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
		all_groups = Group.objects.filter(
			joinedgroup__buyer=user, joinedgroup__deleted_at=None
		)
		if status_filter in ["ongoing", "reached"]:
			all_groups = all_groups.filter(status=status_filter)
	else:
		filter_type = "ongoing"
		all_groups = Group.objects.filter(status="ongoing")
		if user.is_authenticated:
			all_groups = all_groups.exclude(owner=user)
		status_filter = None

	all_groups = all_groups.order_by("-id")

	paginator = Paginator(all_groups, 9)
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
		
		scraped_image_url = request.POST.get("scraped_image_url")
		
		if scraped_image_url:
			files_dict = MultiValueDict()
			
			for key, file_list in request.FILES.lists():
				for file in file_list:
					files_dict.appendlist(key, file)
			
			if not files_dict.get('group-banner'):
				scraped_image_file = download_image_from_url(scraped_image_url, "group_banner")
				if scraped_image_file:
					files_dict['group-banner'] = scraped_image_file

			for i, form in enumerate(product_formset.forms):
				product_banner_field = f"product-{i}-banner"
				if not files_dict.get(product_banner_field):
					scraped_product_image = download_image_from_url(scraped_image_url, f"product_{i}_banner")
					if scraped_product_image:
						files_dict[product_banner_field] = scraped_product_image
			
			group_form = GroupForm(request.POST, files_dict, prefix="group")
			product_formset = ProductFormSet(request.POST, files_dict, prefix="product")

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
		product_formset = ProductFormSet(
			prefix="product", queryset=Product.objects.none()
		)

	limited_config = settings.TINYMCE_LIMITED_CONFIG
	limited_config_json = json.dumps(limited_config)
	context = {
		"url_extractor_form": URLExtractForm(),
		"group_form": group_form,
		"product_form": product_formset,
		"empty_form": product_formset.empty_form,
		"one_week_later": timezone.now() + timedelta(days=7),
		"limited_config_json": limited_config_json,
	}
	return render(request, "groups/new.html", context)


def detail(request, id):
	group = get_object_or_404(Group.objects.select_related("owner"), pk=id)
	user = request.user
	role = "guest"
	order = None

	if user.is_authenticated:
		if group.status == "ongoing":
			if request.method == "POST" and request.POST.get("_method") == "delete":
				if request.POST.get("role") == "owner" and group.owner == user:
					GroupService.leave_group_batch(group=group)
					messages.success(request, "團購已刪除")
					return redirect('groups:index_filtered', filter_type="owned")
				else:
					GroupService.leave_group(user=user, group=group)
					next_url = request.POST.get('next')
					if next_url:
						return redirect(next_url)
					return redirect('groups:index_filtered', filter_type="followed")

			if request.method == "POST":
				try:
					products_data = GroupService.prepare_products_data(request.POST)
					GroupService.join_group(
						user=user, group=group, products_data=products_data
					)
					messages.success(request, "成功更新數量")
				except InsufficientQuantityException as e:
					messages.error(request, str(e))
					return redirect("groups:detail", id=id)
				except ExceedsLimitException as e:
					messages.error(request, str(e))
					return redirect("groups:detail", id=id)
				role = "joiner"

		if group.owner == user:
			role = "owner"
		elif JoinedGroup.objects.filter(
			group=group, buyer=user, deleted_at__isnull=True
		).exists():
			joined_group = JoinedGroup.objects.filter(
				group=group, buyer=user, deleted_at__isnull=True
			).first()
			integrated_products = (
				Product.objects.filter(group=group)
				.annotate(
					user_quantity=Coalesce(
						Subquery(
							JoinedGroupProduct.objects.filter(
								joined_group=joined_group,
								product_id=OuterRef("id"),
								deleted_at__isnull=True,
							).values("quantity")
						),
						0,
					)
				)
				.annotate(subtotal_amount=F("user_quantity") * F("price"))
			)
			group.integrated_products = integrated_products

			if group.status == "reached":
				order = Order.objects.filter(joined_group=joined_group).first()

			role = "joiner"
	else:
		if request.method == "POST" and not request.user.is_authenticated :
			login_url = reverse("users:sessions_new")
			return redirect(f"{login_url}?next={request.path}")

    # 計算剩餘可跟團數量
	current_total = GroupService.get_total(group)
	remaining_limit = max(0, group.min_goal - current_total)

	return render(
		request,
        "groups/detail.html",
        {
            "group": group,
            "role": role,
            "remaining_limit": remaining_limit,
            "order": order,
        },
    )


@login_required
def manage_edit(request, id):
	group = get_object_or_404(Group, id=id)
	if request.user == group.owner:
		if (
			request.method == "POST"
			and group.status == "ongoing"
		):
			group_form = GroupForm(
				request.POST, request.FILES, instance=group, prefix='group'
			)

			if group_form.is_valid():
				with transaction.atomic():
					group_form.save()
					messages.success(request, "團購已更新")
				return redirect("groups:detail", id=id)
			else:
				messages.warning(request, "欄位填寫有誤，請檢查後再試")
		else:
			group_form = GroupForm(instance=group, prefix="group")

		one_week_later = timezone.now() + timedelta(days=7)

		return render(
			request,
			"groups/manage_edit.html",
			{
				'group_form': group_form,
				'one_week_later': one_week_later,
			},
		)
	messages.warning(request, "你沒有權限編輯此團購")
	return redirect("groups:detail", id=id)


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

def extract(request):
	url_extractor_form = URLExtractForm()
	group_form = GroupForm(prefix="group")
	limited_config = settings.TINYMCE_LIMITED_CONFIG
	limited_config_json = json.dumps(limited_config)
	product_formsets = ProductFormSet(prefix="product", queryset=Product.objects.none())

	context = {
		"url_extractor_form": url_extractor_form,
		"group_form": group_form,
		"product_form": product_formsets,
		"empty_form": product_formsets.empty_form,
    	"one_week_later": timezone.now() + timedelta(days=7),
    	"limited_config_json": limited_config_json,
      }
	
	if request.method == "POST":
		url_extractor_form = URLExtractForm(request.POST)
		context["url_extractor_form"] = url_extractor_form

		if url_extractor_form.is_valid():
			url = request.POST.get("url")
			result = scrape_product_url_sync(url)

			if not result.get("success"):
				url_extractor_form.add_error("url", result.get("error", "擷取失敗，請檢查網址"))
				return render(request, "groups/new.html", context)
			
			first_image = result.get("main_image") or (result.get("images", [{}])[0] if result.get("images") else None)

			group_form = GroupForm(prefix="group")
			group_form.fields["name"].initial = result.get("name")
			
			group_description = result.get("description", "")
			if first_image and group_description:
				group_description = f'<img src="{first_image}" alt="商品圖片"><br>{group_description}'
			elif first_image:
				group_description = f'<img src="{first_image}" alt="商品圖片"><br>{result.get("name", "")}'
			
			group_form.fields["description"].initial = group_description

			valid_variants = {k: v for k, v in result.get("variants", {}).items() if isinstance(v, list) and len(v) > 0}

			if valid_variants:
				combinations = list(itertools.product(*valid_variants.values()))
				combo_count = len(combinations)

				DynamicProductFormSet = formset_factory(ProductForm, extra=combo_count, max_num=combo_count)
				product_formsets = DynamicProductFormSet(prefix="product")

				for i, combo in enumerate(combinations):
					if i < len(product_formsets.forms):
						form = product_formsets.forms[i]

						form.initial["name"] = "".join(combo)
						form.initial["price"] = result.get("price", 0)

						product_description = result.get("description", "") or ""
						product_description = re.sub(r"<[^>]+>", "", product_description).strip()
						form.initial["description"] = product_description or result.get("name", "") or ""
			else:
				DynamicProductFormSet = formset_factory(ProductForm, extra=1, max_num=1)
				product_formsets = DynamicProductFormSet(prefix="product")

				if len(product_formsets.forms) > 0:
					form = product_formsets.forms[0]
					form.initial["name"] = result.get("name")
					form.initial["price"] = result.get("price", 0)
			
					product_description = result.get("description", "") or ""
					product_description = re.sub(r"<[^>]+>", "", product_description).strip()
					form.initial["description"] = product_description or result.get("name", "") or ""
			
			context.update({
                    "group_form": group_form,
                    "product_form": product_formsets,
                    "scraped_image": first_image,
					"empty_form": product_formsets.empty_form,
                    "result": result,
                  })
	return render(request, "groups/new.html", context)


def download_image_from_url(image_url, filename_prefix="scraped_image"):
	try:
		if not image_url:
			return None
		
		headers = {
			"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
		}
		if "momoshop.com.tw" in image_url:
			headers["Referer"] = "https://www.momoshop.com.tw/"
			

		response = requests.get(image_url, timeout=10, headers=headers)
		response.raise_for_status()
		
		content_type = response.headers.get("content-type", "")
		if "jpeg" in content_type or "jpg" in content_type:
			extension = ".jpg"
		elif "png" in content_type:
			extension = '.png'
		elif "webp" in content_type:
			extension = ".webp"
		else:
			extension = ".jpg"  # 預設
		
		filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}{extension}"
		return ContentFile(response.content, name=filename)
		
	except Exception:
		return None

