from django.contrib import admin
from .models import User, Reminder, EmailLog

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'birthdate')
    search_fields = ('name', 'email')

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'message', 'send_at', 'sent')
    list_filter = ('sent',)
    search_fields = ('user__name', 'message')

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'to_email', 'subject', 'status', 'sent_at')
    list_filter = ('status',)
    search_fields = ('to_email', 'subject')
