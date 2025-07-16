from rest_framework import generics
from .models import User, Reminder
from .serializers import UserSerializer, ReminderSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .tasks import birthday_task, reminder_task, send_email_task

class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ReminderListCreateView(generics.ListCreateAPIView):
    queryset = Reminder.objects.all()
    serializer_class = ReminderSerializer

class SendEmailView(APIView):
    def post(self, request):
        to_email = request.data.get('to_email')
        subject = request.data.get('subject')
        body = request.data.get('body')
        send_email_task.delay(to_email, subject, body)
        return Response({'message': 'Email yuborildi 🎯'}, status=status.HTTP_200_OK)

class BirthdayTaskView(APIView):
    def post(self, request):
        birthday_task.delay()
        return Response({'message': 'Tug‘ilgan kun uchun email yuborish boshlandi 🎉'}, status=status.HTTP_200_OK)

class ReminderTaskView(APIView):
    def post(self, request):
        reminder_task.delay()
        return Response({'message': 'Eslatma email yuborish boshlandi 🕐'}, status=status.HTTP_200_OK)
