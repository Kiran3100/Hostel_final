import asyncio
import asyncpg


async def create_db():
    conn = await asyncpg.connect("postgresql://postgres:1234@localhost:5432/postgres")
    exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = $1", "stayease_dev"
    )
    if not exists:
        await conn.execute("CREATE DATABASE stayease_dev")
        print("Database stayease_dev created.")
    else:
        print("Database stayease_dev already exists.")
    await conn.close()


asyncio.run(create_db())
