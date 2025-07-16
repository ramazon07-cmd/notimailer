from celery import shared_task
from django.core.mail import send_mail
from .models import EmailLog, User, Reminder
from datetime import date
from django.utils import timezone

@shared_task
def send_email_task(to_email, subject, body):
    try:
        send_mail(subject, body, 'no-reply@example.com', [to_email])
        EmailLog.objects.create(to_email=to_email, subject=subject, body=body, status='Success')
    except:
        EmailLog.objects.create(to_email=to_email, subject=subject, body=body, status='Failed')

@shared_task
def birthday_task():
    today = date.today()
    users = User.objects.filter(birthdate__month=today.month, birthdate__day=today.day)
    for user in users:
        send_email_task.delay(user.email, "Tug'ilgan kun muborak!", f"Salom {user.name}, tug'ilgan kuning bilan!")

@shared_task
def reminder_task():
    now = timezone.now()
    reminders = Reminder.objects.filter(sent=False, send_at__lte=now)
    for r in reminders:
        send_email_task.delay(r.user.email, "Eslatma", r.message)
        r.sent = True
        r.save()
