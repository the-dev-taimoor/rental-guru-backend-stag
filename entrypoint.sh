#!/bin/sh

# Wait for DB
echo "Waiting for postgres..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done
echo "PostgreSQL started"

# Run migrations
python manage.py migrate

# Create superuser if not exists
if [ -n "$SUPERUSER_EMAIL" ] && [ -n "$SUPERUSER_PASSWORD" ]; then
  python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='super-user').exists():
    User.objects.create_superuser('super-user', '$SUPERUSER_EMAIL', '$SUPERUSER_PASSWORD')
END
fi

# Start server
exec python manage.py runserver 0.0.0.0:8000
