"""integrity constraints: unique constraints, check constraints, assigned_at columns

Revision ID: 20260327_0003
Revises: 20260326_0002
Create Date: 2026-03-27 12:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260327_0003"
down_revision = "20260326_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── assigned_at columns — add only if not already present ─────────
    conn = op.get_bind()

    has_admin_assigned_at = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name='admin_hostel_mappings' AND column_name='assigned_at'"
    )).scalar()
    if not has_admin_assigned_at:
        op.add_column(
            "admin_hostel_mappings",
            sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    has_sup_assigned_at = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name='supervisor_hostel_mappings' AND column_name='assigned_at'"
    )).scalar()
    if not has_sup_assigned_at:
        op.add_column(
            "supervisor_hostel_mappings",
            sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    def constraint_exists(name: str, table: str, kind: str) -> bool:
        if kind == "unique":
            return bool(conn.execute(sa.text(
                "SELECT 1 FROM information_schema.table_constraints "
                "WHERE constraint_name=:n AND table_name=:t AND constraint_type='UNIQUE'"
            ), {"n": name, "t": table}).scalar())
        if kind == "check":
            return bool(conn.execute(sa.text(
                "SELECT 1 FROM information_schema.table_constraints "
                "WHERE constraint_name=:n AND table_name=:t AND constraint_type='CHECK'"
            ), {"n": name, "t": table}).scalar())
        return False

    if not constraint_exists("uq_admin_hostel", "admin_hostel_mappings", "unique"):
        op.create_unique_constraint("uq_admin_hostel", "admin_hostel_mappings", ["admin_id", "hostel_id"])

    if not constraint_exists("uq_supervisor_hostel", "supervisor_hostel_mappings", "unique"):
        op.create_unique_constraint("uq_supervisor_hostel", "supervisor_hostel_mappings", ["supervisor_id", "hostel_id"])

    if not constraint_exists("uq_room_hostel_number", "rooms", "unique"):
        op.create_unique_constraint("uq_room_hostel_number", "rooms", ["hostel_id", "room_number"])

    if not constraint_exists("uq_bed_room_number", "beds", "unique"):
        op.create_unique_constraint("uq_bed_room_number", "beds", ["room_id", "bed_number"])

    if not constraint_exists("uq_attendance_student_date", "attendance_records", "unique"):
        # Deduplicate existing rows — keep the most recent per (student_id, date)
        op.execute(sa.text("""
            DELETE FROM attendance_records
            WHERE id NOT IN (
                SELECT DISTINCT ON (student_id, date) id
                FROM attendance_records
                ORDER BY student_id, date, created_at DESC
            )
        """))
        op.create_unique_constraint("uq_attendance_student_date", "attendance_records", ["student_id", "date"])

    if not constraint_exists("ck_booking_dates", "bookings", "check"):
        op.create_check_constraint("ck_booking_dates", "bookings", "check_out_date > check_in_date")

    if not constraint_exists("ck_bed_stay_dates", "bed_stays", "check"):
        op.create_check_constraint("ck_bed_stay_dates", "bed_stays", "end_date > start_date")

    if not constraint_exists("ck_payment_has_context", "payments", "check"):
        op.create_check_constraint(
            "ck_payment_has_context", "payments",
            "booking_id IS NOT NULL OR student_id IS NOT NULL",
        )

    # ── add COMPLETED to bookingstatus enum ───────────────────────────
    op.execute("ALTER TYPE bookingstatus ADD VALUE IF NOT EXISTS 'completed'")


def downgrade() -> None:
    op.drop_constraint("ck_payment_has_context", "payments", type_="check")
    op.drop_constraint("ck_bed_stay_dates", "bed_stays", type_="check")
    op.drop_constraint("ck_booking_dates", "bookings", type_="check")
    op.drop_constraint("uq_attendance_student_date", "attendance_records", type_="unique")
    op.drop_constraint("uq_bed_room_number", "beds", type_="unique")
    op.drop_constraint("uq_room_hostel_number", "rooms", type_="unique")
    op.drop_constraint("uq_supervisor_hostel", "supervisor_hostel_mappings", type_="unique")
    op.drop_constraint("uq_admin_hostel", "admin_hostel_mappings", type_="unique")
    op.drop_column("supervisor_hostel_mappings", "assigned_at")
    op.drop_column("admin_hostel_mappings", "assigned_at")
