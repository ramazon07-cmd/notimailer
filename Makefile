run:
	python manage.py runserver
make:
	python manage.py makemigrations
migrate:
	python manage.py migrate
create:
	python manage.py createsuperuser
worker:
	celery -A notimailer worker -l info
beat:
	celery -A notimailer beat -l info
flower:
	celery -A notimailer flower --port=5555
