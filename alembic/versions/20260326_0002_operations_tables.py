"""operations tables: payments, complaints, attendance, maintenance, notices, mess_menu, subscriptions, reviews

Revision ID: 20260326_0002
Revises: 20260326_0001
Create Date: 2026-03-26 22:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260326_0002"
down_revision = "20260326_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── payments ──────────────────────────────────────────────────────
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("payment_type", sa.String(50), nullable=False),
        sa.Column("payment_method", sa.String(50), nullable=False),
        sa.Column("gateway_order_id", sa.String(120), nullable=True),
        sa.Column("gateway_payment_id", sa.String(120), nullable=True),
        sa.Column("gateway_signature", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("receipt_url", sa.String(500), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.String(255), nullable=True),
        sa.Column("failure_code", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_hostel_id", "payments", ["hostel_id"])
    op.create_index("ix_payments_student_id", "payments", ["student_id"])
    op.create_index("ix_payments_booking_id", "payments", ["booking_id"])
    op.create_index("ix_payments_gateway_order_id", "payments", ["gateway_order_id"])
    op.create_index("ix_payments_status", "payments", ["status"])

    # ── payment_webhook_events ────────────────────────────────────────
    op.create_table(
        "payment_webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_webhook_events_provider", "payment_webhook_events", ["provider"])
    op.create_index("ix_payment_webhook_events_event_type", "payment_webhook_events", ["event_type"])

    # ── complaints ────────────────────────────────────────────────────
    op.create_table(
        "complaints",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complaint_number", sa.String(50), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("complaint_number"),
    )
    op.create_index("ix_complaints_student_id", "complaints", ["student_id"])
    op.create_index("ix_complaints_hostel_id", "complaints", ["hostel_id"])
    op.create_index("ix_complaints_status", "complaints", ["status"])

    # ── complaint_comments ────────────────────────────────────────────
    op.create_table(
        "complaint_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_complaint_comments_complaint_id", "complaint_comments", ["complaint_id"])

    # ── attendance_records ────────────────────────────────────────────
    op.create_table(
        "attendance_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("check_in_time", sa.Time(), nullable=True),
        sa.Column("check_out_time", sa.Time(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("marked_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("method", sa.String(50), nullable=False),
        sa.Column("remarks", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["marked_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attendance_records_student_id", "attendance_records", ["student_id"])
    op.create_index("ix_attendance_records_hostel_id", "attendance_records", ["hostel_id"])
    op.create_index("ix_attendance_records_date", "attendance_records", ["date"])

    # ── maintenance_requests ──────────────────────────────────────────
    op.create_table(
        "maintenance_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reported_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("estimated_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("actual_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("assigned_vendor_name", sa.String(255), nullable=True),
        sa.Column("vendor_contact", sa.String(50), nullable=True),
        sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requires_admin_approval", sa.Boolean(), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["reported_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_maintenance_requests_hostel_id", "maintenance_requests", ["hostel_id"])
    op.create_index("ix_maintenance_requests_status", "maintenance_requests", ["status"])

    # ── notices ───────────────────────────────────────────────────────
    op.create_table(
        "notices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("notice_type", sa.String(100), nullable=False),
        sa.Column("priority", sa.String(50), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("publish_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notices_hostel_id", "notices", ["hostel_id"])
    op.create_index("ix_notices_is_published", "notices", ["is_published"])

    # ── mess_menus ────────────────────────────────────────────────────
    op.create_table(
        "mess_menus",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("week_start_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mess_menus_hostel_id", "mess_menus", ["hostel_id"])
    op.create_index("ix_mess_menus_week_start_date", "mess_menus", ["week_start_date"])

    # ── mess_menu_items ───────────────────────────────────────────────
    op.create_table(
        "mess_menu_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("menu_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("day_of_week", sa.String(20), nullable=False),
        sa.Column("meal_type", sa.String(50), nullable=False),
        sa.Column("item_name", sa.String(255), nullable=False),
        sa.Column("is_veg", sa.Boolean(), nullable=False),
        sa.Column("special_note", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["menu_id"], ["mess_menus.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mess_menu_items_menu_id", "mess_menu_items", ["menu_id"])

    # ── subscriptions ─────────────────────────────────────────────────
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tier", sa.String(50), nullable=False),
        sa.Column("price_monthly", sa.Numeric(10, 2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("auto_renew", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subscriptions_hostel_id", "subscriptions", ["hostel_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])

    # ── reviews ───────────────────────────────────────────────────────
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("visitor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("overall_rating", sa.Float(), nullable=False),
        sa.Column("cleanliness_rating", sa.Float(), nullable=False),
        sa.Column("food_rating", sa.Float(), nullable=False),
        sa.Column("security_rating", sa.Float(), nullable=False),
        sa.Column("value_rating", sa.Float(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("admin_reply", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["visitor_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reviews_hostel_id", "reviews", ["hostel_id"])
    op.create_index("ix_reviews_visitor_id", "reviews", ["visitor_id"])
    op.create_index("ix_reviews_is_published", "reviews", ["is_published"])


def downgrade() -> None:
    for table in [
        "reviews",
        "subscriptions",
        "mess_menu_items",
        "mess_menus",
        "notices",
        "maintenance_requests",
        "attendance_records",
        "complaint_comments",
        "complaints",
        "payment_webhook_events",
        "payments",
    ]:
        op.drop_table(table)
