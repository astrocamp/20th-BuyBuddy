from django.db import transaction
from django.db.models import Sum, F, Count
from django.utils import timezone
from groups.models import Group, JoinedGroup
from products.models import Product, JoinedGroupProduct, ProductImage
from .exceptions import *

class GroupService:

    @staticmethod
    def prepare_products_data(request_post):
        products_data =[]
        for key, value in request_post.items():
                if key.startswith("product-"): 
                    product_id = int(key.split("-")[1])
                    quantity = int(value)
                    if quantity > 0:
                        products_data.append({
                            "id": product_id,
                            "quantity": quantity        
                        })
        return products_data

    @staticmethod
    def get_or_create_joined_group(user, group):
        if group.status != "ongoing":
            raise GroupClosedException("無法加入團購")
        
        joined_group, created = JoinedGroup.objects.get_or_create(
            buyer=user,
            group=group,
            defaults={'deleted_at': None}
        )

        if joined_group.deleted_at is not None:
            joined_group.deleted_at = None
            joined_group.save()
        
        return joined_group, created

    @staticmethod
    def add_products_to_joined_group(joined_group, products_data):
        product_data_map = { item["id"]: item["quantity"] for item in products_data}
        product_ids = list(product_data_map.keys())

        existing_active_products = JoinedGroupProduct.objects.filter(
            joined_group=joined_group,
            product_id__in=product_ids,
            deleted_at__isnull=True
        )

        existing_active_ids = { product.product_id for product in existing_active_products}

        existing_deleted_products = JoinedGroupProduct.objects.filter(
            joined_group=joined_group,
            product_id__in=product_ids,
            deleted_at__isnull=False
        )
        existing_deleted_ids = {p.product_id for p in existing_deleted_products}

        products_to_create = []
        for id, quantity in product_data_map.items():
            if id not in existing_active_ids and id not in existing_deleted_ids:
                created_product = JoinedGroupProduct(
                    joined_group=joined_group,
                    product_id=id,
                    quantity=quantity
                )
                products_to_create.append(created_product)

        products_to_update = []
        for product in existing_active_products:
            product.quantity = product_data_map[product.product_id]
            products_to_update.append(product)

        for product in existing_deleted_products:
            product.quantity = product_data_map[product.product_id]
            product.deleted_at = None
            products_to_update.append(product)

        products_to_delete = JoinedGroupProduct.objects.filter(
            joined_group=joined_group,
            deleted_at__isnull=True
        ).exclude(product_id__in=product_ids)

    
        if products_to_create:
            JoinedGroupProduct.objects.bulk_create(products_to_create)
        
        if products_to_update:
            products_to_restore = [p for p in products_to_update]
            products_to_only_update = [p for p in products_to_update]
            if products_to_restore:
                JoinedGroupProduct.objects.bulk_update(products_to_restore, ["quantity"])
            if products_to_only_update:
                JoinedGroupProduct.objects.bulk_update(products_to_only_update, ["quantity", "deleted_at"])

        if products_to_delete:
            products_to_delete.update(deleted_at=timezone.now())
            

        update_products = JoinedGroupProduct.objects.filter(
            joined_group=joined_group,
            deleted_at__isnull=True
            )

        return [
            {
                "joined_product_id": jg_product.id, 
                "product_id": jg_product.product_id, 
                "quantity": jg_product.quantity
            }
                for jg_product in update_products
        ]
        
    @staticmethod
    @transaction.atomic
    def join_group(user, group, products_data):
        joined_group, is_new_member = GroupService.get_or_create_joined_group(user=user, group=group)
        products = GroupService.add_products_to_joined_group(joined_group=joined_group, products_data=products_data)
        return {
            "joined_group_id":joined_group.id,
            "created": is_new_member,
            "products": products,
            "total_products": len(products)
        }
    
    @staticmethod
    @transaction.atomic
    def leave_group(user, group):
        try:
            joined_group = JoinedGroup.objects.get(buyer=user,group=group)

        except JoinedGroup.DoesNotExist:
            raise JoinedGroupException("找不到此團購或你沒有加入")
        
        joined_group.deleted_at = timezone.now()
        joined_group.save()

        JoinedGroupProduct.objects.filter(joined_group=joined_group).update(deleted_at=timezone.now())

        return True
        

