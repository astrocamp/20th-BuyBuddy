runserver:
	uv run python manage.py runserver

makemigrations:
	uv run python manage.py makemigrations

migrate:
	uv run python manage.py migrate

shell:
	uv run python manage.py shell