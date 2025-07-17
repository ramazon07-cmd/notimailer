# 📧 Notimailer

A personal email reminder service powered by Django + Celery + Redis. Notimailer helps you schedule and send email reminders with robust features including retry logic, rate limiting, and JWT-based authentication.

## 🎯 Features

- **JWT Authentication**: Secure user registration and authentication using Django REST Framework and Simple JWT
- **User Dashboard**: View reminders and email logs with filtering and status tracking
- **Retry Logic**: Failed emails automatically retry up to 3 times with exponential backoff
- **User Permissions**: Users can only access and manage their own reminders
- **Rate Limiting**: Each user is limited to 100 emails per day (Redis-backed)
- **Birthday Emails**: Automatically send birthday greetings to users
- **Email Logging**: Comprehensive tracking of all email attempts with status and error messages
- **Celery Integration**: Asynchronous task processing for email sending and scheduled reminders
- **API Documentation**: Swagger UI available at the root URL

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose

### Installation with Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/notimailer.git
   cd notimailer
   ```

2. Create a `.env` file in the project root with the following variables:
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key
   DB_NAME=notimailer
   DB_USER=postgres
   DB_PASSWORD=yourpassword
   DB_HOST=db
   DB_PORT=5432
   EMAIL_HOST=smtp.yourprovider.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your-email@example.com
   EMAIL_HOST_PASSWORD=your-email-password
   EMAIL_USE_TLS=True
   ```

3. Start the Docker containers:
   ```bash
   docker-compose up -d
   ```

4. Create a superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. Access the application:
   - API Documentation: http://localhost:8000/
   - Admin Dashboard: http://localhost:8000/admin/

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/notimailer.git
   cd notimailer
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file (as described above but set DB_HOST=localhost)

4. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

7. In a separate terminal, start Celery worker:
   ```bash
   celery -A notimailer worker -l info
   ```

8. In another terminal, start Celery beat for scheduled tasks:
   ```bash
   celery -A notimailer beat -l info
   ```

## 📚 API Endpoints

### Authentication
- `POST /api/auth/register/` - Register a new user
- `POST /api/auth/login/` - Login and get JWT tokens
- `POST /api/auth/refresh/` - Refresh JWT token
- `GET /api/auth/profile/` - Get user profile

### Dashboard
- `GET /api/dashboard/` - Get user dashboard with statistics

### Reminders
- `GET /api/reminders/` - List all user reminders
- `POST /api/reminders/` - Create a new reminder
- `GET /api/reminders/{id}/` - Get a specific reminder
- `PUT /api/reminders/{id}/` - Update a reminder
- `DELETE /api/reminders/{id}/` - Delete a reminder
- `GET /api/reminders/upcoming/` - List upcoming reminders
- `GET /api/reminders/sent/` - List sent reminders
- `GET /api/reminders/failed/` - List failed reminders

### Email Logs
- `GET /api/email-logs/` - List all email logs
- `GET /api/email-logs/{id}/` - Get a specific email log

### Send Email
- `POST /api/send-email/` - Send an immediate email

### Tasks
- `POST /api/tasks/birthday/` - Manually trigger birthday email task
- `POST /api/tasks/reminder/` - Manually trigger reminder processing task
- `POST /api/tasks/cleanup-logs/` - Cleanup old email logs

## 📊 Data Models

### User
- Standard Django User model with added UserProfile for birthdate

### Reminder
- `user`: ForeignKey to User
- `title`: CharField
- `message`: TextField
- `scheduled_time`: DateTimeField
- `status`: CharField (pending, sent, failed)
- `created_at`: DateTimeField
- `updated_at`: DateTimeField
- `retry_count`: PositiveSmallIntegerField
- `last_retry`: DateTimeField

### EmailLog
- `reminder`: ForeignKey to Reminder
- `to_email`: EmailField
- `subject`: CharField
- `body`: TextField
- `status`: CharField (success, failed, retry)
- `sent_at`: DateTimeField
- `error_message`: TextField

## 🔧 Project Structure

```
notimailer/
├── core/                   # Main application
│   ├── migrations/         # Database migrations
│   ├── tests/              # Test files
│   ├── admin.py            # Admin configuration
│   ├── apps.py             # App configuration
│   ├── models.py           # Data models
│   ├── serializers.py      # DRF serializers
│   ├── signals.py          # Django signals
│   ├── tasks.py            # Celery tasks
│   ├── urls.py             # URL routing
│   └── views.py            # API views
├── notimailer/             # Project settings
│   ├── celery.py           # Celery configuration
│   ├── schema.py           # API schema/docs
│   ├── settings.py         # Django settings
│   ├── urls.py             # Project URLs
│   └── wsgi.py             # WSGI configuration
├── .gitignore
├── docker-compose.yml      # Docker configuration
├── Dockerfile
├── manage.py
├── Notimailer.postman_collection.json # Postman collection
├── README.md
└── requirements.txt        # Python dependencies
```

## 🧪 Testing

```bash
# Run tests
docker-compose exec web pytest

# Run tests with coverage
docker-compose exec web pytest --cov=core
```

## 📝 Postman Collection

A Postman collection is included in the repository (`Notimailer.postman_collection.json`) to help you test the API endpoints.

## 📜 License

This project is licensed under the MIT License.

## 👨‍💻 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.