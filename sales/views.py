from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from groups.models import Group, JoinedGroup

def index(request):
    groups_list = Group.objects.all()
    context = {
        'groups_list': groups_list,
        'total_groups': groups_list.count(),
    }
    
    if request.user.is_authenticated:
        my_groups = Group.objects.filter(owner=request.user).order_by('-created_at')
        purchases = JoinedGroup.objects.select_related('group').filter(buyer=request.user).order_by('-created_at')
        
        context.update({
            'my_groups': my_groups,
            'total_sales_amount': JoinedGroup.objects.filter(group__owner=request.user).aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'purchases': purchases,
            'total_purchase_amount': purchases.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        })
    
    return render(request, "sales/index.html", context)

@login_required(login_url='/')
def my_sales(request):
    my_groups_list = Group.objects.filter(owner=request.user).order_by('-created_at')
    
    total_amount = JoinedGroup.objects.filter(
        group__owner=request.user
    ).aggregate(total=Sum('total_amount')).get('total') or 0
    
    return render(request, 'sales/my_group.html', {
        'my_groups': my_groups_list,
        'total_amount': total_amount,
    })

@login_required(login_url='/')
def purchase_list(request):
    purchases = JoinedGroup.objects.select_related('group', 'buyer').filter(
        buyer=request.user
    ).order_by('-created_at')
    
    total_amount = purchases.aggregate(total=Sum('total_amount')).get('total') or 0
    
    return render(request, 'sales/purchases.html', {
        'purchases': purchases,
        'total_amount': total_amount,
    })