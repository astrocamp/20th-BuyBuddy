from django.core.management.base import BaseCommand
from groups.models import Group, JoinedGroup
from users.models import User
from notifications.services.base import (
    send_notifications_for_group_status_change,
    send_notification_for_new_order,
    send_notification_for_order_status_change,
    send_notification_for_new_order_message,
)
from orders.models import Order, OrderMessage, _generate_unique_number
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Triggers various notification types to test email and in-site notifications.'

    def _create_test_data(self):
        self.stdout.write(self.style.SUCCESS("Creating test data..."))
        # Fetch existing users
        owner = User.objects.get(id=5)  # ostrlchblue0609@gmail.com
        follower = User.objects.get(id=4)  # a0970760494@gmail.com

        # Create a new test group with the fetched owner
        group = Group.objects.create(
            name='Test Group for Notification', owner=owner, min_goal=100, goal_choice='quantity', status='pending'
        )
        self.stdout.write(self.style.SUCCESS(f"Created new Group ID: {group.id} for testing with owner {owner.email}."))

        # Add follower to the group
        joined_group = JoinedGroup.objects.create(buyer=follower, group=group)
        self.stdout.write(self.style.SUCCESS(f"Follower {follower.email} joined Group {group.id}."))

        # Create a test order
        order = Order.objects.create(
            order_number=_generate_unique_number(), user=follower, group=group, joined_group=joined_group, amount=Decimal('50.00'),
            order_status=Order.OrderStatus.PENDING
        )
        self.stdout.write(self.style.SUCCESS(f"Created new Order ID: {order.id} for testing."))
        return owner, follower, group, joined_group, order

    def _test_group_status_change(self, group):
        self.stdout.write(self.style.SUCCESS("\n--- Testing Group Status Change Notification ---"))
        original_status = group.status
        group.start_group() # Transition to ongoing first
        group.save()
        group.reached() # Then to reached
        group.save()
        send_notifications_for_group_status_change(group)
        self.stdout.write(self.style.SUCCESS(f"Group {group.id} status changed to 'reached'. Notifications triggered."))

    def _test_new_order_notification(self, order):
        self.stdout.write(self.style.SUCCESS("\n--- Testing New Order Notification ---"))
        send_notification_for_new_order(order)
        self.stdout.write(self.style.SUCCESS(f"New order notification triggered for Order ID: {order.id}."))

    def _test_order_status_change_notification(self, order):
        self.stdout.write(self.style.SUCCESS("\n--- Testing Order Status Change Notification ---"))
        
        # Ensure order is in PENDING state to start transitions
        order.order_status = Order.OrderStatus.PENDING
        order.save()

        # Test transition to PROCESSING
        order.mark_as_processing() 
        order.save()
        send_notification_for_order_status_change(order, order.get_order_status_display())
        self.stdout.write(self.style.SUCCESS(f"Order {order.id} status changed to '{order.get_order_status_display()}'. Notifications triggered."))

        # Test transition to SHIPPED
        order.mark_as_shipped()
        order.save()
        send_notification_for_order_status_change(order, order.get_order_status_display())
        self.stdout.write(self.style.SUCCESS(f"Order {order.id} status changed to '{order.get_order_status_display()}'. Notifications triggered."))

        # Test transition to COMPLETED
        order.mark_as_completed()
        order.save()
        send_notification_for_order_status_change(order, order.get_order_status_display())
        self.stdout.write(self.style.SUCCESS(f"Order {order.id} status changed to '{order.get_order_status_display()}'. Notifications triggered."))

    def _test_new_order_message_notification(self, order, sender, receiver):
        self.stdout.write(self.style.SUCCESS("\n--- Testing New Order Message Notification ---"))
        order_message = OrderMessage.objects.create(
            order=order, sender=sender, receiver=receiver, content="This is a test message."
        )
        send_notification_for_new_order_message(order_message)
        self.stdout.write(self.style.SUCCESS(f"New order message notification triggered for Order ID: {order.id}."))

    def handle(self, *args, **options):
        try:
            owner, follower, group, joined_group, order = self._create_test_data()

            self._test_group_status_change(group)
            self._test_new_order_notification(order)
            self._test_order_status_change_notification(order)
            self._test_new_order_message_notification(order, follower, owner) # Follower sends message to owner
            self._test_new_order_message_notification(order, owner, follower) # Owner sends message to follower

            self.stdout.write(self.style.SUCCESS("\nAll notification tests executed successfully. Please check your email inboxes (ostrlchblue0609@gmail.com, a0970760494@gmail.com) and in-site notifications, and provide Celery worker logs."))

        except Exception as e:
            logger.error(f"Error executing notification test command: {e}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"Error executing notification test command: {e}"))
