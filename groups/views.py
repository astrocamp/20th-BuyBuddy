from django.shortcuts import render, redirect, get_object_or_404
from .models import Group, JoinedGroup
from .forms import GroupForm, ProductFormSet
from products.models import ProductImage
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .services.exceptions import *
from .services.group_services import GroupService
from django.utils import timezone
from datetime import datetime


def index(request):
	groups = Group.objects.filter(status="ongoing")
	return render(request, "groups/index.html", {"groups": groups})

def new(request):
	product_form = ProductFormSet(prefix='product')
	group_form = GroupForm(prefix='group')
	return render(request, 'groups/new.html', {'product_form': product_form, 'group_form': group_form})

@login_required
def owned(request):
	groups = Group.objects.filter(owner=request.user)
	
	if request.method == "POST":
		
		if request.POST.get("_method") == "delete":
			group_id = request.POST.get("group-id")
			group = get_object_or_404(Group, pk=group_id)
			if group.owner != request.user:
				messages.warning(request, "您無權刪除此團購")
				return redirect('groups:owned')
			group.delete()
			messages.success(request, "團購已刪除")
			return redirect('groups:owned')

		group_form = GroupForm(request.POST, request.FILES, prefix="group")
		if group_form.is_valid():
			with transaction.atomic():
				group = group_form.save(commit=False)
				group.owner = request.user
				group.status = "ongoing"
				group.save()	
				product_formset = ProductFormSet(request.POST, instance=group, prefix="product")
				if product_formset.is_valid():
					products = product_formset.save(commit=False)
					for i, product in enumerate(products):
						product.group = group
						product.save()
						image = request.FILES.get(f"url_{i}")
						if image:
							ProductImage.objects.create(
									product=product,
									url=image,
									order=0
							)			
					messages.success(request, "團購已建立")
					return redirect("groups:owned")
		else:
			messages.warning(request, "欄位填寫有誤，請檢查後再試")
		return render(request, "groups/new.html", {"product_form": product_formset, "group_form": group_form})	
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
	group_form = GroupForm(instance=group, prefix="group")
	product_formset = ProductFormSet(instance=group, prefix="product")
	if request.user != group.owner:
		messages.warning(request, "您無權編輯此團購")
		return redirect("groups:owned")
	if request.method == "POST":
		try:
			update = []
			if "group-deadline" in request.POST:
				deadline = request.POST.get("group-deadline")
				if not deadline:
					raise ValueError("請選擇截止日期")
				deadline_naive = datetime.strptime(deadline, '%Y-%m-%d')
				deadline_aware = timezone.make_aware(deadline_naive)
				group.deadline = deadline_aware
				update.append("deadline")


			if "group-min_goal" in request.POST:
				min_goal_str = request.POST.get("group-min_goal")
				if not min_goal_str:
					raise ValueError("請選擇最小目標")

				min_goal = int(min_goal_str)
				if min_goal < 1:
					raise ValueError("最小目標不能小於1")
				group.min_goal = min_goal
				update.append("min_goal")

			if update:
				group.save(update_fields=update)
			
			messages.success(request, "團購已更新")
			return redirect("groups:owned")
		except (ValueError, TypeError) as error:
			messages.warning(request, f"欄位填寫有誤，{str(error)}")
			return render(request, "groups/manage_edit.html", {"product_form": product_formset, "group_form": group_form})
	return render(request, "groups/manage_edit.html", {"product_form": product_formset, "group_form": group_form})
	


