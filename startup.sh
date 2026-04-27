#!/bin/bash

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Seed data (optional - only for development)
if [ "$APP_ENV" != "production" ]; then
    echo "Seeding development data..."
    python -m scripts.seed_data
fi

# Start the application
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT