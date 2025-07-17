import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from core.models import UserProfile, Reminder, EmailLog

class TestUserProfile(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            birthdate=timezone.now().date()
        )
    
    def test_profile_creation(self):
        """Test UserProfile can be created"""
        self.assertEqual(self.profile.user.username, 'testuser')
        self.assertEqual(str(self.profile), "testuser's profile")

class TestReminder(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.reminder = Reminder.objects.create(
            user=self.user,
            title='Test Reminder',
            message='This is a test reminder',
            scheduled_time=timezone.now() + timedelta(days=1),
            status='pending'
        )
    
    def test_reminder_creation(self):
        """Test Reminder can be created"""
        self.assertEqual(self.reminder.title, 'Test Reminder')
        self.assertEqual(self.reminder.status, 'pending')
        self.assertEqual(self.reminder.retry_count, 0)
        self.assertEqual(str(self.reminder), "Test Reminder - testuser")
    
    def test_reminder_status_update(self):
        """Test Reminder status can be updated"""
        self.reminder.status = 'sent'
        self.reminder.save()
        updated_reminder = Reminder.objects.get(id=self.reminder.id)
        self.assertEqual(updated_reminder.status, 'sent')

class TestEmailLog(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.reminder = Reminder.objects.create(
            user=self.user,
            title='Test Reminder',
            message='This is a test reminder',
            scheduled_time=timezone.now(),
            status='pending'
        )
        self.log = EmailLog.objects.create(
            reminder=self.reminder,
            to_email='test@example.com',
            subject='Test Subject',
            body='Test Body',
            status='success'
        )
    
    def test_email_log_creation(self):
        """Test EmailLog can be created"""
        self.assertEqual(self.log.to_email, 'test@example.com')
        self.assertEqual(self.log.status, 'success')
        self.assertEqual(str(self.log), "Email to test@example.com - success")
    
    def test_email_log_with_error(self):
        """Test EmailLog can store error messages"""
        log = EmailLog.objects.create(
            reminder=self.reminder,
            to_email='test@example.com',
            subject='Failed Email',
            body='This email failed',
            status='failed',
            error_message='SMTP connection failed'
        )
        self.assertEqual(log.status, 'failed')
        self.assertEqual(log.error_message, 'SMTP connection failed')