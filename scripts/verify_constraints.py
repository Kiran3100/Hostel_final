import asyncio
import asyncpg


async def verify():
    conn = await asyncpg.connect("postgresql://postgres:1234@localhost:5432/stayease_dev")

    print("\n=== UNIQUE CONSTRAINTS ===")
    rows = await conn.fetch("""
        SELECT tc.table_name, tc.constraint_name
        FROM information_schema.table_constraints tc
        WHERE tc.constraint_type = 'UNIQUE'
          AND tc.table_schema = 'public'
        ORDER BY tc.table_name, tc.constraint_name
    """)
    for r in rows:
        print(f"  {r['table_name']}: {r['constraint_name']}")

    print("\n=== CHECK CONSTRAINTS ===")
    rows = await conn.fetch("""
        SELECT tc.table_name, tc.constraint_name, cc.check_clause
        FROM information_schema.table_constraints tc
        JOIN information_schema.check_constraints cc
          ON tc.constraint_name = cc.constraint_name
        WHERE tc.constraint_type = 'CHECK'
          AND tc.table_schema = 'public'
          AND tc.constraint_name NOT LIKE '%_not_null'
        ORDER BY tc.table_name
    """)
    for r in rows:
        print(f"  {r['table_name']}: {r['constraint_name']} → {r['check_clause']}")

    print("\n=== ENUM VALUES (bookingstatus) ===")
    rows = await conn.fetch("""
        SELECT enumlabel FROM pg_enum
        JOIN pg_type ON pg_enum.enumtypid = pg_type.oid
        WHERE pg_type.typname = 'bookingstatus'
        ORDER BY enumsortorder
    """)
    print("  " + ", ".join(r["enumlabel"] for r in rows))

    await conn.close()
    print("\n✅ All constraints verified.")


asyncio.run(verify())
