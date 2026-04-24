import asyncio
import asyncpg


async def check():
    conn = await asyncpg.connect("postgresql://postgres:1234@localhost:5432/stayease_dev")
    rows = await conn.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
    )
    print(f"Found {len(rows)} tables:")
    for r in rows:
        print(" ", r["tablename"])
    await conn.close()


asyncio.run(check())
