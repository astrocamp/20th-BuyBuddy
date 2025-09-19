from django.contrib.auth import get_user_model
from django.test import TestCase

from groups.models import Group, JoinedGroup
from groups.services.exceptions import ExceedsLimitException
from groups.services.group_services import GroupService
from products.models import JoinedGroupProduct, Product

User = get_user_model()


class CheckAmountLimitTestCase(TestCase):
    def setUp(self):
        # 創建測試用戶
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass"
        )

        # 創建另一個用戶（用於測試多用戶情況）
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass"
        )

        # 創建數量目標團購 (目標: 100個)
        self.quantity_group = Group.objects.create(
            name="數量測試團購",
            owner=self.user,
            min_goal=100,
            goal_choice="quantity",
            status="ongoing",
            description="測試用團購",
        )

        # 創建金額目標團購 (目標: 10000元)
        self.amount_group = Group.objects.create(
            name="金額測試團購",
            owner=self.user,
            min_goal=10000,
            goal_choice="amount",
            status="ongoing",
            description="測試用團購",
        )

        # 創建測試商品
        self.product1 = Product.objects.create(
            group=self.quantity_group, name="商品1", price=100, description="測試商品1"
        )

        self.product2 = Product.objects.create(
            group=self.quantity_group, name="商品2", price=200, description="測試商品2"
        )

        # 為金額團購創建商品
        self.amount_product1 = Product.objects.create(
            group=self.amount_group,
            name="金額商品1",
            price=500,
            description="金額測試商品1",
        )

    def test_new_user_quantity_within_limit(self):
        """測試新用戶購買數量在限制內"""
        products_data = [
            {"id": self.product1.id, "quantity": 50},
            {"id": self.product2.id, "quantity": 30},
        ]

        # 應該不會拋出異常
        try:
            GroupService.check_amount_limit(
                self.user, self.quantity_group, products_data
            )
        except ExceedsLimitException:
            self.fail("新用戶購買80個商品應該在100個限制內")

    def test_new_user_quantity_exceeds_limit(self):
        """測試新用戶購買數量超過限制"""
        products_data = [
            {"id": self.product1.id, "quantity": 70},
            {"id": self.product2.id, "quantity": 50},
        ]

        # 應該拋出異常
        with self.assertRaises(ExceedsLimitException):
            GroupService.check_amount_limit(
                self.user, self.quantity_group, products_data
            )

    def test_existing_user_update_quantity_within_limit(self):
        """測試現有用戶更新購買數量在限制內"""
        # 先讓用戶加入團購並購買一些商品
        joined_group = JoinedGroup.objects.create(
            buyer=self.user, group=self.quantity_group
        )

        # 用戶已經購買了30個商品1
        JoinedGroupProduct.objects.create(
            joined_group=joined_group, product=self.product1, quantity=30
        )

        # 現在用戶想要將商品1數量改為60個，商品2購買20個
        # 淨增加量 = (60 + 20) - 30 = 50個
        products_data = [
            {"id": self.product1.id, "quantity": 60},
            {"id": self.product2.id, "quantity": 20},
        ]

        # 應該不會拋出異常（總共增加50個，在限制內）
        try:
            GroupService.check_amount_limit(
                self.user, self.quantity_group, products_data
            )
        except ExceedsLimitException:
            self.fail("用戶更新後淨增加50個應該在限制內")

    def test_existing_user_update_quantity_exceeds_limit(self):
        """測試現有用戶更新購買數量超過限制"""
        # 讓其他用戶先購買70個商品，使團購接近限制
        other_joined_group = JoinedGroup.objects.create(
            buyer=self.other_user, group=self.quantity_group
        )
        JoinedGroupProduct.objects.create(
            joined_group=other_joined_group, product=self.product1, quantity=70
        )

        # 當前用戶已經購買了10個商品1
        joined_group = JoinedGroup.objects.create(
            buyer=self.user, group=self.quantity_group
        )
        JoinedGroupProduct.objects.create(
            joined_group=joined_group, product=self.product1, quantity=10
        )

        # 現在用戶想要將商品1數量改為50個
        # 淨增加量 = 50 - 10 = 40個
        # 總量會變成 70 + 50 = 120個，超過100個限制
        products_data = [{"id": self.product1.id, "quantity": 50}]

        # 應該拋出異常
        with self.assertRaises(ExceedsLimitException):
            GroupService.check_amount_limit(
                self.user, self.quantity_group, products_data
            )

    def test_amount_goal_within_limit(self):
        """測試金額目標在限制內（1.2倍限制）"""
        products_data = [
            {"id": self.amount_product1.id, "quantity": 20}  # 20 * 500 = 10000元
        ]

        # 應該不會拋出異常（10000元在12000元限制內）
        try:
            GroupService.check_amount_limit(self.user, self.amount_group, products_data)
        except ExceedsLimitException:
            self.fail("10000元應該在12000元限制內")

    def test_amount_goal_exceeds_limit(self):
        """測試金額目標超過限制"""
        products_data = [
            {"id": self.amount_product1.id, "quantity": 25}  # 25 * 500 = 12500元
        ]

        # 應該拋出異常（12500元超過12000元限制）
        with self.assertRaises(ExceedsLimitException):
            GroupService.check_amount_limit(self.user, self.amount_group, products_data)

    def test_existing_user_amount_update_within_limit(self):
        """測試現有用戶金額更新在限制內"""
        # 用戶已經購買了5000元
        joined_group = JoinedGroup.objects.create(
            buyer=self.user, group=self.amount_group
        )
        JoinedGroupProduct.objects.create(
            joined_group=joined_group,
            product=self.amount_product1,
            quantity=10,  # 10 * 500 = 5000元
        )

        # 現在用戶想要改為購買20個（總價10000元）
        # 淨增加量 = 10000 - 5000 = 5000元
        products_data = [{"id": self.amount_product1.id, "quantity": 20}]

        try:
            GroupService.check_amount_limit(self.user, self.amount_group, products_data)
        except ExceedsLimitException:
            self.fail("淨增加5000元應該在限制內")
