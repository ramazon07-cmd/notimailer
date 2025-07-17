from django.contrib import admin
from django.utils.html import format_html
from .models import UserProfile, Reminder, EmailLog
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

class ReminderAdmin(admin.ModelAdmin):
    list_display = ('title', 'user_info', 'scheduled_time', 'status', 'retry_count', 'created_at')
    list_filter = ('status', 'created_at', 'scheduled_time')
    search_fields = ('title', 'message', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'retry_count', 'last_retry')
    
    def user_info(self, obj):
        return f"{obj.user.username} ({obj.user.email})"
    
    user_info.short_description = 'User'

class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('subject', 'to_email', 'sent_at', 'status', 'related_reminder')
    list_filter = ('status', 'sent_at')
    search_fields = ('subject', 'to_email', 'body')
    readonly_fields = ('sent_at',)
    
    def related_reminder(self, obj):
        if obj.reminder:
            return format_html('<a href="{}">{}</a>', 
                              f'/admin/core/reminder/{obj.reminder.id}/change/', 
                              obj.reminder.title)
        return '-'
    
    related_reminder.short_description = 'Reminder'

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_email', 'birthdate')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    
    def user_email(self, obj):
        return obj.user.email
    
    user_email.short_description = 'Email'

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Reminder, ReminderAdmin)
admin.site.register(EmailLog, EmailLogAdmin)