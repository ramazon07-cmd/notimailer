from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    SendEmailView, 
    BirthdayTaskView, 
    ReminderTaskView,
    RegisterView,
    UserProfileView,
    ReminderViewSet,
    EmailLogViewSet,
    DashboardView,
    CleanupLogsView,
    MyTokenObtainPairView
)

# Create a router for viewsets
router = DefaultRouter()
router.register(r'reminders', ReminderViewSet, basename='reminder')
router.register(r'email-logs', EmailLogViewSet, basename='email_log')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/profile/', UserProfileView.as_view(), name='user_profile'),

    # API endpoints
    path('', include(router.urls)),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('send-email/', SendEmailView.as_view(), name='send_email'),

    # Task runner endpoints
    path('tasks/birthday/', BirthdayTaskView.as_view(), name='run_birthday'),
    path('tasks/reminder/', ReminderTaskView.as_view(), name='run_reminder'),
    path('tasks/cleanup-logs/', CleanupLogsView.as_view(), name='cleanup_logs'),

    # Frontend test page
]
