from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    birthdate = models.DateField()

class Reminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    send_at = models.DateTimeField()
    sent = models.BooleanField(default=False)

class EmailLog(models.Model):
    to_email = models.EmailField()
    subject = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=10)
    sent_at = models.DateTimeField(auto_now_add=True)
