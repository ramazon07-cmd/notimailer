import logging
from celery import shared_task
from django.core.mail import send_mail
from .models import EmailLog, Reminder, UserProfile
from datetime import date, timedelta
from django.utils import timezone
from django.conf import settings
from celery.exceptions import MaxRetriesExceededError
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_email_task(self, to_email, subject, body, reminder_id=None):
    """
    Send an email with retry logic. 
    Will retry up to 3 times with exponential backoff if sending fails.
    """
    logger.info(f"Attempting to send email to {to_email}: {subject}")
    
    try:
        send_mail(subject, body, 'no-reply@example.com', [to_email])
        
        log_entry = EmailLog.objects.create(
            to_email=to_email, 
            subject=subject, 
            body=body, 
            status='success'
        )
        
        # Update the reminder if provided
        if reminder_id:
            try:
                reminder = Reminder.objects.get(id=reminder_id)
                reminder.status = 'sent'
                reminder.save()
                log_entry.reminder = reminder
                log_entry.save()
            except Reminder.DoesNotExist:
                logger.error(f"Reminder with ID {reminder_id} not found")
        
        logger.info(f"Successfully sent email to {to_email}")
        return True
    
    except Exception as exc:
        # Log the error
        error_message = str(exc)
        logger.error(f"Failed to send email to {to_email}: {error_message}")
        
        # Create or update the log entry
        log_entry = EmailLog.objects.create(
            to_email=to_email, 
            subject=subject, 
            body=body, 
            status='failed',
            error_message=error_message
        )
        
        # Update the reminder if provided
        if reminder_id:
            try:
                reminder = Reminder.objects.get(id=reminder_id)
                reminder.retry_count += 1
                reminder.last_retry = timezone.now()
                
                if self.request.retries >= self.max_retries:
                    reminder.status = 'failed'
                else:
                    reminder.status = 'pending'
                
                reminder.save()
                log_entry.reminder = reminder
                log_entry.save()
            except Reminder.DoesNotExist:
                logger.error(f"Reminder with ID {reminder_id} not found")
        
        # Retry with exponential backoff
        try:
            countdown = 2 ** self.request.retries * 60  # 1 min, 2 min, 4 min
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for email to {to_email}")
            return False

@shared_task
def birthday_task():
    """
    Task to send birthday emails to users whose birthdate is today.
    """
    logger.info("Running birthday email task")
    today = date.today()
    
    # Get profiles with today's birthdate
    profiles = UserProfile.objects.filter(
        birthdate__month=today.month, 
        birthdate__day=today.day
    ).select_related('user')
    
    sent_count = 0
    for profile in profiles:
        user = profile.user
        if user.email:
            logger.info(f"Sending birthday email to {user.email}")
            subject = "Happy Birthday!"
            body = f"Hello {user.first_name or user.username},\n\nWishing you a wonderful birthday and a great year ahead!\n\nBest regards,\nNotimailer Team"
            send_email_task.delay(user.email, subject, body)
            sent_count += 1
    
    logger.info(f"Birthday task completed. Sent {sent_count} emails.")
    return sent_count

@shared_task
def reminder_task():
    """
    Task to process and send due reminders.
    """
    logger.info("Running reminder task")
    now = timezone.now()
    
    # Get reminders that are due and not yet sent or failed
    reminders = Reminder.objects.filter(
        status='pending',
        scheduled_time__lte=now
    ).select_related('user')
    
    sent_count = 0
    for reminder in reminders:
        if reminder.user.email:
            logger.info(f"Processing reminder: {reminder.title} for {reminder.user.email}")
            
            subject = f"Reminder: {reminder.title}"
            body = reminder.message
            
            # Send the email with the reminder ID for tracking
            send_email_task.delay(
                reminder.user.email,
                subject,
                body,
                reminder_id=reminder.id
            )
            sent_count += 1
    
    logger.info(f"Reminder task completed. Processed {sent_count} reminders.")
    return sent_count

@shared_task
def clean_old_logs():
    """
    Task to clean up old email logs (older than 30 days)
    """
    threshold_date = timezone.now() - timedelta(days=30)
    old_logs = EmailLog.objects.filter(sent_at__lt=threshold_date)
    count = old_logs.count()
    old_logs.delete()
    logger.info(f"Cleaned up {count} old email logs")
    return count
