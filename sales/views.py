from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.apps import apps
from .models import SalesIndex, SalesPurchase

def index(request):
    sales_list = SalesIndex.objects.select_related('owner').order_by('-id')

    groups_list = []
    try:
        if apps.is_installed('groups'):
            Group = apps.get_model('groups', 'Group')
            groups_list = Group.objects.select_related('owner').order_by('-created_at')
    except (LookupError, ImportError):
        pass
    
    return render(request, "sales/index.html", {
        'sales_list': sales_list,
        'groups_list': groups_list,
        'total_sales': sales_list.count(),
        'total_groups': len(groups_list),
    })

@login_required
def my_sales(request):
    my_sales_list = SalesIndex.objects.filter(owner=request.user).order_by('-id')
    
    total_revenue = SalesPurchase.objects.filter(
        sales_index__owner=request.user
    ).aggregate(total=Sum('total_amount')).get('total') or 0
    
    my_groups = []
    try:
        if apps.is_installed('groups'):
            Group = apps.get_model('groups', 'Group')
            my_groups = Group.objects.filter(owner=request.user).order_by('-created_at')
    except (LookupError, ImportError):
        pass
    
    return render(request, 'sales/my_group.html', {
        'my_sales_list': my_sales_list,
        'my_groups': my_groups,
        'total_revenue': total_revenue,
    })

@login_required
def purchase_list(request):
    purchases = (
        SalesPurchase.objects
        .select_related('sales_index', 'user')
        .filter(user_id=request.user.id)
        .order_by('-purchase_date')
    )
    
    total_amount = purchases.aggregate(total=Sum('total_amount')).get('total') or 0
    
    return render(request, 'sales/purchases.html', {
        'purchases': purchases,
        'total_amount': total_amount,
    })
