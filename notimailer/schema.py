from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="📧 Notimailer API Documentation",
      default_version='v1',
      description="""
      # Notimailer - Personal Email Reminder Service
      
      Welcome to the Notimailer API! This service allows users to schedule and manage email reminders with powerful features including retry logic, rate limiting, and detailed tracking.
      
      ## 🎯 Features
      * **JWT Authentication** - Secure user authentication and authorization
      * **Email Scheduling** - Schedule reminders for future delivery
      * **Dashboard Statistics** - Track reminder statuses and email delivery
      * **Rate Limiting** - 100 emails per day per user
      * **Retry Logic** - Automatic retries with exponential backoff for failed emails
      * **User Permissions** - Users can only access their own data
      
      ## 📚 API Endpoints
      
      ### Authentication
      * `/api/auth/register/` - Register a new user
      * `/api/auth/login/` - Login and get JWT tokens
      * `/api/auth/refresh/` - Refresh JWT token
      * `/api/auth/profile/` - Get user profile
      
      ### Reminders
      * `/api/reminders/` - CRUD operations for reminders
      * `/api/reminders/upcoming/` - List upcoming reminders
      * `/api/reminders/sent/` - List sent reminders
      * `/api/reminders/failed/` - List failed reminders
      
      ### Dashboard & Email Management
      * `/api/dashboard/` - User statistics and upcoming reminders
      * `/api/email-logs/` - View email sending history
      * `/api/send-email/` - Send immediate emails
      
      ### Task Management
      * `/api/tasks/birthday/` - Trigger birthday email task
      * `/api/tasks/reminder/` - Trigger reminder processing
      * `/api/tasks/cleanup-logs/` - Clean up old email logs
      """,
      terms_of_service="https://notimailer.com/terms/",
      contact=openapi.Contact(email="support@notimailer.com", name="Notimailer Support Team"),
      license=openapi.License(name="MIT License", url="https://opensource.org/licenses/MIT"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)
