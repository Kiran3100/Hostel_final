#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed data (only if tables are empty)
python -c "
import asyncio
from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal
from app.models.user import User

async def check_and_seed():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).limit(1))
        users = result.scalars().all()
        if not users:
            print('No users found, seeding data...')
            from scripts.seed_data import StayEaseSeeder
            seeder = StayEaseSeeder(session)
            await seeder.run()
        else:
            print(f'Database already has {len(users)} users, skipping seed')

asyncio.run(check_and_seed())
"

# Start the app
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT