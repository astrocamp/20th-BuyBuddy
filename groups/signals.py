from django.db.models.signals import post_save, post_delete
from django.db.models import Sum, F
from django.dispatch import receiver
from products.models import JoinedGroupProduct
from .models import Group

def get_total(group):
    products = JoinedGroupProduct.objects.filter(
        joined_group__group=group,
        deleted_at__isnull=True
        )
    totals = products.aggregate(
        total_quantity=Sum("quantity"), 
        total_amount=Sum(F("quantity") * F("product__price"))
        )
    if group.goal_choice == "quantity":
        return totals.get("total_quantity", 0)
    elif group.goal_choice == "amount":
        return totals.get("total_amount", 0)
    else:
        return 0
    
def get_progress(current_total, min_goal):
    progress = 0
    if min_goal > 0:
        progress = min((current_total / min_goal) * 100, 100)
        progress = round(progress) 
    return progress

@receiver(post_save, sender=JoinedGroupProduct)
def product_added(sender, instance, created, **kwargs):
    group = instance.joined_group.group
    current_total = get_total(group)
    current_progress = get_progress(current_total, group.min_goal)
    group.total = current_total
    group.current_progress = current_progress
    group.save(update_fields=["total",  "current_progress"])

