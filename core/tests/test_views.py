import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Reminder, EmailLog, UserProfile
from django.utils import timezone
from datetime import timedelta
import json
from unittest.mock import patch

class TestJWTAuthentication(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123',
            'password2': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_user_registration(self):
        """Test user registration"""
        response = self.client.post(
            self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')
        self.assertTrue(UserProfile.objects.filter(user__username='testuser').exists())

    def test_user_login_and_token_generation(self):
        """Test user can login and get JWT tokens"""
        # Create a user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        UserProfile.objects.create(user=user)

        # Login
        response = self.client.post(
            self.login_url,
            {'username': 'testuser', 'password': 'testpassword123'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_authentication_required_for_protected_endpoints(self):
        """Test that protected endpoints require authentication"""
        dashboard_url = reverse('dashboard')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestReminderViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpassword123'
        )
        UserProfile.objects.create(user=self.user)
        UserProfile.objects.create(user=self.other_user)
        
        # Create some reminders for both users
        self.reminder1 = Reminder.objects.create(
            user=self.user,
            title='User Reminder 1',
            message='This is a test reminder for the main user',
            scheduled_time=timezone.now() + timedelta(days=1),
            status='pending'
        )
        self.reminder2 = Reminder.objects.create(
            user=self.other_user,
            title='Other User Reminder',
            message='This is a test reminder for the other user',
            scheduled_time=timezone.now() + timedelta(days=1),
            status='pending'
        )
        
        # Authenticate the client
        self.client.force_authenticate(user=self.user)
        self.reminder_list_url = reverse('reminder-list')

    def test_get_reminders_only_returns_user_reminders(self):
        """Test that only the user's reminders are returned"""
        response = self.client.get(self.reminder_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'User Reminder 1')
    
    def test_create_reminder(self):
        """Test creating a new reminder"""
        data = {
            'title': 'New Reminder',
            'message': 'This is a new reminder',
            'scheduled_time': (timezone.now() + timedelta(days=2)).isoformat()
        }
        response = self.client.post(self.reminder_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reminder.objects.count(), 3)
        self.assertEqual(Reminder.objects.filter(user=self.user).count(), 2)
    
    def test_update_reminder(self):
        """Test updating a reminder"""
        detail_url = reverse('reminder-detail', kwargs={'pk': self.reminder1.pk})
        data = {
            'title': 'Updated Title',
            'message': 'Updated message',
            'scheduled_time': self.reminder1.scheduled_time.isoformat()
        }
        response = self.client.put(detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reminder1.refresh_from_db()
        self.assertEqual(self.reminder1.title, 'Updated Title')
    
    def test_cannot_update_other_users_reminder(self):
        """Test that a user cannot update another user's reminder"""
        detail_url = reverse('reminder-detail', kwargs={'pk': self.reminder2.pk})
        data = {
            'title': 'Hacked Title',
            'message': 'Hacked message',
            'scheduled_time': self.reminder2.scheduled_time.isoformat()
        }
        response = self.client.put(detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.reminder2.refresh_from_db()
        self.assertNotEqual(self.reminder2.title, 'Hacked Title')


class TestDashboardView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        UserProfile.objects.create(user=self.user)
        
        # Create some reminders with different statuses
        now = timezone.now()
        
        # Pending reminders (upcoming)
        for i in range(3):
            Reminder.objects.create(
                user=self.user,
                title=f'Pending Reminder {i}',
                message=f'This is pending reminder {i}',
                scheduled_time=now + timedelta(days=i+1),
                status='pending'
            )
        
        # Sent reminders
        for i in range(2):
            reminder = Reminder.objects.create(
                user=self.user,
                title=f'Sent Reminder {i}',
                message=f'This is sent reminder {i}',
                scheduled_time=now - timedelta(days=i+1),
                status='sent'
            )
            # Create email logs for these reminders
            EmailLog.objects.create(
                reminder=reminder,
                to_email=self.user.email,
                subject=reminder.title,
                body=reminder.message,
                status='success'
            )
        
        # Failed reminder
        failed_reminder = Reminder.objects.create(
            user=self.user,
            title='Failed Reminder',
            message='This is a failed reminder',
            scheduled_time=now - timedelta(days=1),
            status='failed'
        )
        EmailLog.objects.create(
            reminder=failed_reminder,
            to_email=self.user.email,
            subject=failed_reminder.title,
            body=failed_reminder.message,
            status='failed',
            error_message='Test error'
        )
        
        # Authenticate the client
        self.client.force_authenticate(user=self.user)
        self.dashboard_url = reverse('dashboard')

    def test_dashboard_view_returns_correct_counts(self):
        """Test that the dashboard view returns correct counts"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check counts
        self.assertEqual(response.data['total_reminders'], 6)
        self.assertEqual(response.data['pending_reminders'], 3)
        self.assertEqual(response.data['sent_reminders'], 2)
        self.assertEqual(response.data['failed_reminders'], 1)
        
        # Check that upcoming reminders are included
        self.assertEqual(len(response.data['upcoming_reminders']), 3)
        
        # Check that recent logs are included
        self.assertEqual(len(response.data['recent_logs']), 3)


class TestSendEmailView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        UserProfile.objects.create(user=self.user)
        
        # Authenticate the client
        self.client.force_authenticate(user=self.user)
        self.send_email_url = reverse('send_email')

    @patch('core.tasks.send_email_task.delay')
    def test_send_email_view(self, mock_send_email_task):
        """Test sending an email via the API"""
        data = {
            'to_email': 'recipient@example.com',
            'subject': 'Test Email',
            'body': 'This is a test email.'
        }
        response = self.client.post(self.send_email_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that a reminder was created
        self.assertEqual(Reminder.objects.count(), 1)
        reminder = Reminder.objects.first()
        self.assertEqual(reminder.title, 'Test Email')
        self.assertEqual(reminder.message, 'This is a test email.')
        
        # Check that the task was called
        mock_send_email_task.assert_called_once_with(
            'recipient@example.com', 
            'Test Email', 
            'This is a test email.',
            reminder_id=reminder.id
        )

    def test_send_email_validation(self):
        """Test validation for sending emails"""
        # Missing to_email
        data = {
            'subject': 'Test Email',
            'body': 'This is a test email.'
        }
        response = self.client.post(self.send_email_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)