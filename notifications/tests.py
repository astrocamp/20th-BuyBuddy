import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from groups.models import Group
from notifications.services.base import send_notifications_for_group_status_change
from notifications.models import Notification, UserNotification

User = get_user_model()

class NotificationServiceTest(TestCase):
    def setUp(self):
        self.user_owner = User.objects.create_user(
            username='owner', email='owner@example.com', password='password', is_verified=True
        )
        self.user_follower = User.objects.create_user(
            username='follower', email='follower@example.com', password='password', is_verified=True
        )
        self.group = Group.objects.create(
            name='Test Group', owner=self.user_owner, min_goal=100, goal_choice='quantity', status='ongoing'
        )

    @patch('notifications.services.mail_service.send_group_notification_email')
    @patch('notifications.services.base.send_owner_email_task.delay')
    @patch('notifications.services.base.send_followers_email_task.delay')
    @patch('groups.models.Group.get_followers') # Mock get_followers to control follower list
    def test_send_notifications_for_group_status_change(self, mock_get_followers, mock_send_followers_email_task_delay, mock_send_owner_email_task_delay, mock_send_group_notification_email):
        # Configure mock for get_followers
        mock_get_followers.return_value = [self.user_follower.id]

        # Ensure no notifications exist initially
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(UserNotification.objects.count(), 0)

        # Call the function to test
        send_notifications_for_group_status_change(self.group)

        # Assert that in-app notifications were created
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(UserNotification.objects.count(), 2) # Owner and follower

        # Assert that email tasks were delayed
        mock_send_owner_email_task_delay.assert_called_once_with(self.group.id, '進行中') # Assuming 'ongoing' status_display
        mock_send_followers_email_task_delay.assert_called_once_with(self.group.id, '進行中')

        # Assert that the mail_service function was NOT directly called (it's called by Celery task)
        mock_send_group_notification_email.assert_not_called()

        # Verify the content of the created notification
        notification = Notification.objects.first()
        self.assertIn(self.group.name, notification.title)
        self.assertIn(self.group.name, notification.content)
        self.assertEqual(notification.group, self.group)

        # Verify UserNotifications
        user_notifications = UserNotification.objects.all()
        self.assertIn(self.user_owner, [un.user for un in user_notifications])
        self.assertIn(self.user_follower, [un.user for un in user_notifications])
        for un in user_notifications:
            self.assertEqual(un.notification, notification)
            self.assertFalse(un.is_read)
