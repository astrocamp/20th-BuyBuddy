import logging

from django.db import transaction
from django.db.models import Sum, F
from django.utils import timezone

from groups.models import JoinedGroup
from orders.services import create_orders
from products.models import JoinedGroupProduct
from .exceptions import (
    GroupClosedException,
    InsufficientQuantityException,
    ExceedsLimitException,
    JoinedGroupException,
)
from groups.models import Group


class GroupService:
    @staticmethod
    def get_total(group):
        products = JoinedGroupProduct.objects.filter(
            joined_group__group=group, deleted_at__isnull=True
        )
        totals = products.aggregate(
            total_quantity=Sum("quantity"),
            total_amount=Sum(F("quantity") * F("product__price")),
        )
        if group.goal_choice == "quantity":
            return totals.get("total_quantity") or 0
        elif group.goal_choice == "amount":
            return totals.get("total_amount") or 0
        else:
            return 0

    @staticmethod
    def get_progress(current_total, min_goal):
        progress = 0
        if min_goal > 0:
            progress = min((current_total / min_goal) * 100, 100)
            progress = round(progress)
        return progress

    @staticmethod
    def update_total_and_progress(group):
        current_total = GroupService.get_total(group)
        current_progress = GroupService.get_progress(current_total, group.min_goal)
        group.total = current_total
        group.current_progress = current_progress
        group.save(update_fields=["total", "current_progress"])

    @staticmethod
    def is_reached(group):
        return GroupService.get_total(group) >= group.min_goal

    @staticmethod
    def prepare_products_data(request_post):
        products_data = []
        for key, value in request_post.items():
            if key.startswith("product-"):
                product_id = int(key.split("-")[1])
                quantity = int(value)
                if quantity > 0:
                    products_data.append({"id": product_id, "quantity": quantity})
        return products_data

    @staticmethod
    def get_or_create_joined_group(user, group):
        if group.status != "ongoing":
            raise GroupClosedException("無法加入團購")

        joined_group, created = JoinedGroup.objects.get_or_create(
            buyer=user, group=group, defaults={"deleted_at": None}
        )

        if joined_group.deleted_at is not None:
            joined_group.deleted_at = None
            joined_group.save()

        return joined_group, created

    @staticmethod
    def add_products_to_joined_group(joined_group, products_data):
        product_data_map = {item["id"]: item["quantity"] for item in products_data}
        if not product_data_map:
            raise InsufficientQuantityException("商品數量不能全部為0")
        product_ids = list(product_data_map.keys())

        existing_active_products = JoinedGroupProduct.objects.filter(
            joined_group=joined_group,
            product_id__in=product_ids,
            deleted_at__isnull=True,
        )

        existing_active_ids = {
            product.product_id for product in existing_active_products
        }

        existing_deleted_products = JoinedGroupProduct.objects.filter(
            joined_group=joined_group,
            product_id__in=product_ids,
            deleted_at__isnull=False,
        )
        existing_deleted_ids = {p.product_id for p in existing_deleted_products}

        products_to_create = []
        for id, quantity in product_data_map.items():
            if id not in existing_active_ids and id not in existing_deleted_ids:
                created_product = JoinedGroupProduct(
                    joined_group=joined_group, product_id=id, quantity=quantity
                )
                products_to_create.append(created_product)

        products_to_update = []
        for product in existing_active_products:
            product.quantity = product_data_map[product.product_id]
            products_to_update.append(product)

        products_to_restore = []
        for product in existing_deleted_products:
            product.quantity = product_data_map[product.product_id]
            product.deleted_at = None
            products_to_restore.append(product)

        products_to_delete = JoinedGroupProduct.objects.filter(
            joined_group=joined_group, deleted_at__isnull=True
        ).exclude(product_id__in=product_ids)

        if products_to_create:
            JoinedGroupProduct.objects.bulk_create(products_to_create)

        if products_to_update:
            JoinedGroupProduct.objects.bulk_update(products_to_update, ["quantity"])

        if products_to_restore:
            JoinedGroupProduct.objects.bulk_update(
                products_to_restore, ["quantity", "deleted_at"]
            )

        if products_to_delete.exists():
            products_to_delete.update(deleted_at=timezone.now())

        update_products = JoinedGroupProduct.objects.filter(
            joined_group=joined_group, deleted_at__isnull=True
        )

        return [
            {
                "joined_product_id": jg_product.id,
                "product_id": jg_product.product_id,
                "quantity": jg_product.quantity,
            }
            for jg_product in update_products
        ]

    @staticmethod
    @transaction.atomic
    def join_group(user, group, products_data):
        GroupService.check_amount_limit(user, group, products_data)
        joined_group, is_new_member = GroupService.get_or_create_joined_group(
            user=user, group=group
        )
        products = GroupService.add_products_to_joined_group(
            joined_group=joined_group, products_data=products_data
        )
        GroupService.update_total_and_progress(group)

        goal_reached = GroupService._handle_goal_reached_if_needed(group)

        return {
            "joined_group_id": joined_group.id,
            "created": is_new_member,
            "products": products,
            "total_products": len(products),
            "goal_reached": goal_reached,
        }

    @staticmethod
    def _handle_goal_reached_if_needed(group):
        if GroupService.is_reached(group):
            # 執行狀態轉換
            group.reached()
            group.save(update_fields=["status"])

            # 安排在交易提交後建立訂單
            transaction.on_commit(
                lambda: GroupService._create_orders_after_commit(group.id)
            )

            return True
        return False

    @staticmethod
    def _create_orders_after_commit(group_id):
        """在交易提交後建立訂單"""
        try:
            group = Group.objects.get(id=group_id)

            if group.status == "reached" or GroupService.is_reached(group):
                create_orders(group)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"建立訂單失敗 (Group ID: {group_id}): {e}", exc_info=True)

    @staticmethod
    @transaction.atomic
    def leave_group(user, group):
        try:
            joined_group = JoinedGroup.objects.get(buyer=user, group=group)

        except JoinedGroup.DoesNotExist:
            raise JoinedGroupException("找不到此團購或你沒有加入")

        joined_group.deleted_at = timezone.now()
        joined_group.save()
        JoinedGroupProduct.objects.filter(joined_group=joined_group).update(
            deleted_at=timezone.now()
        )

        GroupService.update_total_and_progress(group)

        return True

    @staticmethod
    @transaction.atomic
    def leave_group_batch(group):
        now = timezone.now()
        group.deleted_at = now
        group.cancel_group()
        group.save()

        joiners_qs = JoinedGroup.objects.filter(group=group, deleted_at__isnull=True)
        joiner_ids = list(joiners_qs.values_list("id", flat=True))
        joiners_qs.update(deleted_at=now)

        JoinedGroupProduct.objects.filter(joined_group_id__in=joiner_ids).update(
            deleted_at=now
        )

        GroupService.update_total_and_progress(group)

        return True

    @staticmethod
    def check_amount_limit(user, group, products_data):
        current_total = GroupService.get_total(group=group)
        product_data_map = {item["id"]: item["quantity"] for item in products_data}
        try:
            joined_group = JoinedGroup.objects.get(
                buyer=user, group=group, deleted_at__isnull=True
            )
            existing_products = JoinedGroupProduct.objects.filter(
                joined_group=joined_group, deleted_at__isnull=True
            )

        except JoinedGroup.DoesNotExist:
            existing_products = JoinedGroupProduct.objects.none()

        if group.goal_choice == "quantity":
            existing_quantity = (
                existing_products.aggregate(total=Sum("quantity"))["total"] or 0
            )
            updated_quantity = sum(product_data_map.values())
            net_quantity = updated_quantity - existing_quantity
            if current_total + net_quantity > group.min_goal:
                raise ExceedsLimitException("超過可購買上限")
