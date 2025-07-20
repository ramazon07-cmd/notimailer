from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    birthdate = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

class Reminder(models.Model):
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('sent', _('Sent')),
        ('failed', _('Failed')),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    title = models.CharField(max_length=200)
    message = models.TextField()
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    retry_count = models.PositiveSmallIntegerField(default=0)
    last_retry = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class EmailLog(models.Model):
    STATUS_CHOICES = (
        ('success', _('Success')),
        ('failed', _('Failed')),
        ('retry', _('Retry')),
    )

    reminder = models.ForeignKey(Reminder, on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    to_email = models.EmailField()
    subject = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    sent_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Email to {self.to_email} - {self.status}"
