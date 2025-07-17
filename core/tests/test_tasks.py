import pytest
from unittest.mock import patch, Mock, call
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from core.models import Reminder, EmailLog, UserProfile
from core.tasks import send_email_task, birthday_task, reminder_task, clean_old_logs
from celery.exceptions import Retry

class TestSendEmailTask(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.reminder = Reminder.objects.create(
            user=self.user,
            title='Test Reminder',
            message='This is a test reminder',
            scheduled_time=timezone.now(),
            status='pending'
        )

    @patch('core.tasks.send_mail')
    def test_send_email_task_success(self, mock_send_mail):
        """Test successful email sending"""
        # Configure the mock to return success
        mock_send_mail.return_value = 1
        
        # Call the task
        result = send_email_task(
            to_email='recipient@example.com',
            subject='Test Subject',
            body='Test Body',
            reminder_id=self.reminder.id
        )
        
        # Check that the email was sent
        mock_send_mail.assert_called_once_with(
            'Test Subject',
            'Test Body',
            'no-reply@example.com',
            ['recipient@example.com']
        )
        
        # Check that the task returned True
        self.assertTrue(result)
        
        # Check that the EmailLog was created
        log = EmailLog.objects.filter(to_email='recipient@example.com').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, 'success')
        self.assertEqual(log.reminder, self.reminder)
        
        # Check that the reminder status was updated
        self.reminder.refresh_from_db()
        self.assertEqual(self.reminder.status, 'sent')

    @patch('core.tasks.send_mail')
    @patch('core.tasks.send_email_task.retry')
    def test_send_email_task_failure_and_retry(self, mock_retry, mock_send_mail):
        """Test email sending failure with retry"""
        # Configure the mock to raise an exception
        exception = Exception('Test exception')
        mock_send_mail.side_effect = exception
        
        # Configure the retry mock to raise Retry exception
        mock_retry.side_effect = Retry()
        
        # Set up the task with request attributes
        task = send_email_task
        task.request = Mock()
        task.request.retries = 0
        task.max_retries = 3
        
        # Call the task and expect it to retry
        with self.assertRaises(Retry):
            send_email_task(
                to_email='recipient@example.com',
                subject='Test Subject',
                body='Test Body',
                reminder_id=self.reminder.id
            )
        
        # Check that the EmailLog was created
        log = EmailLog.objects.filter(to_email='recipient@example.com').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, 'failed')
        self.assertEqual(log.reminder, self.reminder)
        
        # Check that retry was called with exponential backoff
        mock_retry.assert_called_once_with(exc=exception, countdown=60)
        
        # Check that the reminder was updated
        self.reminder.refresh_from_db()
        self.assertEqual(self.reminder.retry_count, 1)
        self.assertEqual(self.reminder.status, 'pending')

    @patch('core.tasks.send_mail')
    @patch('core.tasks.send_email_task.retry')
    def test_max_retries_exceeded(self, mock_retry, mock_send_mail):
        """Test behavior when max retries are exceeded"""
        # Configure the mock to raise an exception
        exception = Exception('Test exception')
        mock_send_mail.side_effect = exception
        
        # Configure the retry mock to raise MaxRetriesExceededError
        mock_retry.side_effect = Exception('Max retries exceeded')
        
        # Set up the task with request attributes
        task = send_email_task
        task.request = Mock()
        task.request.retries = 3  # Max retries reached
        task.max_retries = 3
        
        # Call the task
        result = send_email_task(
            to_email='recipient@example.com',
            subject='Test Subject',
            body='Test Body',
            reminder_id=self.reminder.id
        )
        
        # Check that the task returns False
        self.assertFalse(result)
        
        # Check that the reminder status was updated to failed
        self.reminder.refresh_from_db()
        self.assertEqual(self.reminder.status, 'failed')
        self.assertEqual(self.reminder.retry_count, 1)


class TestBirthdayTask(TestCase):
    def setUp(self):
        # Create users with various birthdates
        today = timezone.now().date()
        
        # User with birthday today
        self.birthday_user = User.objects.create_user(
            username='birthdayuser',
            email='birthday@example.com',
            password='testpassword123',
            first_name='Birthday',
            last_name='User'
        )
        UserProfile.objects.create(
            user=self.birthday_user,
            birthdate=today.replace(year=today.year - 30)  # 30 years ago, same month and day
        )
        
        # User with birthday tomorrow
        self.tomorrow_user = User.objects.create_user(
            username='tomorrowuser',
            email='tomorrow@example.com',
            password='testpassword123'
        )
        UserProfile.objects.create(
            user=self.tomorrow_user,
            birthdate=(today + timedelta(days=1)).replace(year=today.year - 25)
        )
        
        # User with birthday yesterday
        self.yesterday_user = User.objects.create_user(
            username='yesterdayuser',
            email='yesterday@example.com',
            password='testpassword123'
        )
        UserProfile.objects.create(
            user=self.yesterday_user,
            birthdate=(today - timedelta(days=1)).replace(year=today.year - 40)
        )

    @patch('core.tasks.send_email_task.delay')
    def test_birthday_task(self, mock_send_email_task):
        """Test that birthday task sends emails to users with birthdays today"""
        # Run the task
        result = birthday_task()
        
        # Check that the task returned 1 (number of emails sent)
        self.assertEqual(result, 1)
        
        # Check that send_email_task was called once for the birthday user
        mock_send_email_task.assert_called_once()
        args, kwargs = mock_send_email_task.call_args
        self.assertEqual(kwargs['to_email'], 'birthday@example.com')
        self.assertEqual(kwargs['subject'], 'Happy Birthday!')
        self.assertIn('Birthday', kwargs['body'])


class TestReminderTask(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        now = timezone.now()
        
        # Create reminders with different scheduled times
        
        # Due reminder (should be processed)
        self.due_reminder = Reminder.objects.create(
            user=self.user,
            title='Due Reminder',
            message='This reminder is due now',
            scheduled_time=now - timedelta(minutes=5),
            status='pending'
        )
        
        # Future reminder (should not be processed)
        self.future_reminder = Reminder.objects.create(
            user=self.user,
            title='Future Reminder',
            message='This reminder is for the future',
            scheduled_time=now + timedelta(days=1),
            status='pending'
        )
        
        # Already sent reminder (should not be processed)
        self.sent_reminder = Reminder.objects.create(
            user=self.user,
            title='Sent Reminder',
            message='This reminder was already sent',
            scheduled_time=now - timedelta(hours=1),
            status='sent'
        )
        
        # Failed reminder (should not be processed)
        self.failed_reminder = Reminder.objects.create(
            user=self.user,
            title='Failed Reminder',
            message='This reminder failed',
            scheduled_time=now - timedelta(hours=2),
            status='failed'
        )

    @patch('core.tasks.send_email_task.delay')
    def test_reminder_task(self, mock_send_email_task):
        """Test that reminder task processes due reminders"""
        # Run the task
        result = reminder_task()
        
        # Check that the task returned 1 (number of reminders processed)
        self.assertEqual(result, 1)
        
        # Check that send_email_task was called once for the due reminder
        mock_send_email_task.assert_called_once_with(
            'test@example.com',
            'Reminder: Due Reminder',
            'This reminder is due now',
            reminder_id=self.due_reminder.id
        )
        
        # Verify that other reminders were not processed
        self.future_reminder.refresh_from_db()
        self.sent_reminder.refresh_from_db()
        self.failed_reminder.refresh_from_db()
        
        self.assertEqual(self.future_reminder.status, 'pending')
        self.assertEqual(self.sent_reminder.status, 'sent')
        self.assertEqual(self.failed_reminder.status, 'failed')


class TestCleanOldLogs(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.reminder = Reminder.objects.create(
            user=self.user,
            title='Test Reminder',
            message='This is a test reminder',
            scheduled_time=timezone.now(),
            status='sent'
        )
        
        now = timezone.now()
        
        # Create some old logs (> 30 days)
        old_date = now - timedelta(days=31)
        for i in range(5):
            EmailLog.objects.create(
                reminder=self.reminder,
                to_email='test@example.com',
                subject=f'Old Log {i}',
                body=f'This is an old log {i}',
                status='success',
                sent_at=old_date
            )
        
        # Create some recent logs (< 30 days)
        recent_date = now - timedelta(days=15)
        for i in range(3):
            EmailLog.objects.create(
                reminder=self.reminder,
                to_email='test@example.com',
                subject=f'Recent Log {i}',
                body=f'This is a recent log {i}',
                status='success',
                sent_at=recent_date
            )

    def test_clean_old_logs(self):
        """Test that clean_old_logs removes only logs older than 30 days"""
        # Verify initial count
        self.assertEqual(EmailLog.objects.count(), 8)
        
        # Run the task
        result = clean_old_logs()
        
        # Check that the task returned 5 (number of logs deleted)
        self.assertEqual(result, 5)
        
        # Verify that only recent logs remain
        self.assertEqual(EmailLog.objects.count(), 3)
        for log in EmailLog.objects.all():
            self.assertEqual(log.subject.startswith('Recent'), True)