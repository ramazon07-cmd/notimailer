from django.urls import path
from .views import SendEmailView, BirthdayTaskView, ReminderTaskView, UserListCreateView, ReminderListCreateView

urlpatterns = [
    path('send-email/', SendEmailView.as_view(), name='send_email'),
    path('run-birthday/', BirthdayTaskView.as_view(), name='run_birthday'),
    path('run-reminder/', ReminderTaskView.as_view(), name='run_reminder'),
    path('users/', UserListCreateView.as_view(), name='user_list_create'),
    path('reminders/', ReminderListCreateView.as_view(), name='reminder_list_create'),
]
