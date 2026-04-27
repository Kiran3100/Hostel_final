#!/bin/bash

# Exit on error
set -e

echo "=========================================="
echo "  StayEase Backend - Starting up..."
echo "=========================================="

# Print environment info
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"

# Run database migrations
echo ""
echo "📦 Running database migrations..."
alembic upgrade head

# Check if we should seed data (optional - only for development)
if [ "$SEED_DATA" = "true" ]; then
    echo ""
    echo "🌱 Seeding database with initial data..."
    python -m scripts.seed_data
fi

# Print startup message
echo ""
echo "=========================================="
echo "  🚀 Starting StayEase API Server..."
echo "=========================================="
echo ""

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info