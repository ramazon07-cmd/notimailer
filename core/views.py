from rest_framework import generics, status, viewsets, filters
from django.contrib.auth.models import User
from .models import Reminder, EmailLog, UserProfile
from .serializers import UserSerializer, ReminderSerializer, EmailLogSerializer, MyTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone
from django.db.models import Q
from .tasks import birthday_task, reminder_task, send_email_task, clean_old_logs
from rest_framework.throttling import UserRateThrottle
import logging

logger = logging.getLogger(__name__)

class EmailRateThrottle(UserRateThrottle):
    scope = 'emails'
    
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'message']
    ordering_fields = ['scheduled_time', 'created_at', 'status']
    ordering = ['-scheduled_time']

    def get_queryset(self):
        """
        This view should return only reminders for the currently authenticated user.
        """
        user = self.request.user
        # Check if user is authenticated before filtering
        if not user.is_authenticated:
            return Reminder.objects.none()
        return Reminder.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def upcoming(self):
        """Return upcoming reminders"""
        now = timezone.now()
        reminders = self.get_queryset().filter(
            scheduled_time__gt=now,
            status='pending'
        ).order_by('scheduled_time')[:5]
        serializer = self.get_serializer(reminders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def sent(self):
        """Return sent reminders"""
        reminders = self.get_queryset().filter(status='sent').order_by('-scheduled_time')
        serializer = self.get_serializer(reminders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def failed(self):
        """Return failed reminders"""
        reminders = self.get_queryset().filter(status='failed').order_by('-scheduled_time')
        serializer = self.get_serializer(reminders, many=True)
        return Response(serializer.data)
        
class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EmailLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        This view should return only email logs related to the current user's reminders.
        """
        user = self.request.user
        # Check if user is authenticated before filtering
        if not user.is_authenticated:
            return EmailLog.objects.none()
        return EmailLog.objects.filter(reminder__user=user).order_by('-sent_at')

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Return dashboard statistics for the current user
        """
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
        now = timezone.now()
        
        # Get counts
        total_reminders = Reminder.objects.filter(user=user).count()
        pending_reminders = Reminder.objects.filter(user=user, status='pending').count()
        sent_reminders = Reminder.objects.filter(user=user, status='sent').count()
        failed_reminders = Reminder.objects.filter(user=user, status='failed').count()
        
        # Get upcoming reminders
        upcoming_reminders = Reminder.objects.filter(
            user=user,
            status='pending',
            scheduled_time__gt=now
        ).order_by('scheduled_time')[:5]
        
        # Get recent email logs
        recent_logs = EmailLog.objects.filter(
            reminder__user=user
        ).order_by('-sent_at')[:10]
        
        # Serialize the data
        upcoming_serializer = ReminderSerializer(upcoming_reminders, many=True)
        logs_serializer = EmailLogSerializer(recent_logs, many=True)
        
        return Response({
            'total_reminders': total_reminders,
            'pending_reminders': pending_reminders,
            'sent_reminders': sent_reminders,
            'failed_reminders': failed_reminders,
            'upcoming_reminders': upcoming_serializer.data,
            'recent_logs': logs_serializer.data
        })

class SendEmailView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [EmailRateThrottle]
    
    def post(self, request):
        """
        Send an immediate email (not a scheduled reminder)
        """
        to_email = request.data.get('to_email')
        subject = request.data.get('subject')
        body = request.data.get('body')
        
        if not all([to_email, subject, body]):
            return Response({
                'error': 'Please provide to_email, subject, and body'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a reminder for tracking
        reminder = Reminder.objects.create(
            user=request.user,
            title=subject,
            message=body,
            scheduled_time=timezone.now(),
            status='pending'
        )
        
        # Send the email
        send_email_task.delay(to_email, subject, body, reminder_id=reminder.id)
        
        return Response({
            'message': 'Email sent successfully',
            'reminder_id': reminder.id
        }, status=status.HTTP_200_OK)

class BirthdayTaskView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Manually trigger the birthday email task
        """
        task = birthday_task.delay()
        return Response({
            'message': 'Birthday email task started',
            'task_id': task.id
        }, status=status.HTTP_200_OK)

class ReminderTaskView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Manually trigger the reminder processing task
        """
        task = reminder_task.delay()
        return Response({
            'message': 'Reminder processing task started',
            'task_id': task.id
        }, status=status.HTTP_200_OK)

class CleanupLogsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Manually trigger cleanup of old email logs
        """
        task = clean_old_logs.delay()
        return Response({
            'message': 'Log cleanup task started',
            'task_id': task.id
        }, status=status.HTTP_200_OK)

# Frontend view removed
