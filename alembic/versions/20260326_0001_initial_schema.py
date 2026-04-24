"""initial schema

Revision ID: 20260326_0001
Revises:
Create Date: 2026-03-26 21:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260326_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Enum("SUPER_ADMIN", "HOSTEL_ADMIN", "SUPERVISOR", "STUDENT", "VISITOR", name="userrole"), nullable=False),
        sa.Column("profile_picture_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False),
        sa.Column("is_phone_verified", sa.Boolean(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_phone"), "users", ["phone"], unique=True)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    op.create_table(
        "hostels",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("hostel_type", sa.Enum("BOYS", "GIRLS", "COED", name="hosteltype"), nullable=False),
        sa.Column("status", sa.Enum("PENDING_APPROVAL", "ACTIVE", "INACTIVE", "SUSPENDED", "REJECTED", name="hostelstatus"), nullable=False),
        sa.Column("address_line1", sa.String(length=255), nullable=False),
        sa.Column("address_line2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=120), nullable=False),
        sa.Column("country", sa.String(length=120), nullable=False),
        sa.Column("pincode", sa.String(length=20), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("rules_and_regulations", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_hostels_city"), "hostels", ["city"], unique=False)
    op.create_index(op.f("ix_hostels_name"), "hostels", ["name"], unique=False)
    op.create_index(op.f("ix_hostels_slug"), "hostels", ["slug"], unique=True)
    op.create_index(op.f("ix_hostels_state"), "hostels", ["state"], unique=False)

    op.create_table(
        "rooms",
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_number", sa.String(length=50), nullable=False),
        sa.Column("floor", sa.Integer(), nullable=False),
        sa.Column("room_type", sa.Enum("SINGLE", "DOUBLE", "TRIPLE", "DORMITORY", name="roomtype"), nullable=False),
        sa.Column("total_beds", sa.Integer(), nullable=False),
        sa.Column("daily_rent", sa.Numeric(10, 2), nullable=False),
        sa.Column("monthly_rent", sa.Numeric(10, 2), nullable=False),
        sa.Column("security_deposit", sa.Numeric(10, 2), nullable=False),
        sa.Column("dimensions", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rooms_hostel_id"), "rooms", ["hostel_id"], unique=False)
    op.create_index(op.f("ix_rooms_room_type"), "rooms", ["room_type"], unique=False)

    op.create_table(
        "beds",
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bed_number", sa.String(length=50), nullable=False),
        sa.Column("status", sa.Enum("AVAILABLE", "OCCUPIED", "MAINTENANCE", "RESERVED", name="bedstatus"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_beds_hostel_id"), "beds", ["hostel_id"], unique=False)
    op.create_index(op.f("ix_beds_room_id"), "beds", ["room_id"], unique=False)

    op.create_table(
        "bookings",
        sa.Column("booking_number", sa.String(length=50), nullable=False),
        sa.Column("visitor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bed_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("booking_mode", sa.Enum("DAILY", "MONTHLY", name="bookingmode"), nullable=False),
        sa.Column("status", sa.Enum("DRAFT", "PAYMENT_PENDING", "PENDING_APPROVAL", "APPROVED", "REJECTED", "CHECKED_IN", "CHECKED_OUT", "CANCELLED", name="bookingstatus"), nullable=False),
        sa.Column("check_in_date", sa.Date(), nullable=False),
        sa.Column("check_out_date", sa.Date(), nullable=False),
        sa.Column("total_nights", sa.Integer(), nullable=True),
        sa.Column("total_months", sa.Integer(), nullable=True),
        sa.Column("base_rent_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("security_deposit", sa.Numeric(10, 2), nullable=False),
        sa.Column("booking_advance", sa.Numeric(10, 2), nullable=False),
        sa.Column("grand_total", sa.Numeric(10, 2), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(length=50), nullable=True),
        sa.Column("occupation", sa.String(length=255), nullable=True),
        sa.Column("institution", sa.String(length=255), nullable=True),
        sa.Column("current_address", sa.Text(), nullable=True),
        sa.Column("id_type", sa.String(length=100), nullable=True),
        sa.Column("id_document_url", sa.String(length=500), nullable=True),
        sa.Column("emergency_contact_name", sa.String(length=255), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(length=30), nullable=True),
        sa.Column("emergency_contact_relationship", sa.String(length=100), nullable=True),
        sa.Column("guardian_name", sa.String(length=255), nullable=True),
        sa.Column("guardian_phone", sa.String(length=30), nullable=True),
        sa.Column("special_requirements", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ),
        sa.ForeignKeyConstraint(["bed_id"], ["beds.id"], ),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ),
        sa.ForeignKeyConstraint(["visitor_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bookings_bed_id"), "bookings", ["bed_id"], unique=False)
    op.create_index(op.f("ix_bookings_booking_mode"), "bookings", ["booking_mode"], unique=False)
    op.create_index(op.f("ix_bookings_booking_number"), "bookings", ["booking_number"], unique=True)
    op.create_index(op.f("ix_bookings_hostel_id"), "bookings", ["hostel_id"], unique=False)
    op.create_index(op.f("ix_bookings_room_id"), "bookings", ["room_id"], unique=False)
    op.create_index(op.f("ix_bookings_status"), "bookings", ["status"], unique=False)
    op.create_index(op.f("ix_bookings_visitor_id"), "bookings", ["visitor_id"], unique=False)

    op.create_table(
        "students",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bed_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_number", sa.String(length=50), nullable=False),
        sa.Column("check_in_date", sa.Date(), nullable=False),
        sa.Column("check_out_date", sa.Date(), nullable=True),
        sa.Column("status", sa.Enum("ACTIVE", "CHECKED_OUT", "ON_LEAVE", name="studentstatus"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["bed_id"], ["beds.id"], ),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_id"),
    )
    op.create_index(op.f("ix_students_bed_id"), "students", ["bed_id"], unique=False)
    op.create_index(op.f("ix_students_hostel_id"), "students", ["hostel_id"], unique=False)
    op.create_index(op.f("ix_students_room_id"), "students", ["room_id"], unique=False)
    op.create_index(op.f("ix_students_student_number"), "students", ["student_number"], unique=True)
    op.create_index(op.f("ix_students_user_id"), "students", ["user_id"], unique=False)

    op.create_table(
        "bed_stays",
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bed_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.Enum("RESERVED", "ACTIVE", "COMPLETED", "CANCELLED", name="bedstaystatus"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["bed_id"], ["beds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bed_stays_bed_id"), "bed_stays", ["bed_id"], unique=False)
    op.create_index(op.f("ix_bed_stays_booking_id"), "bed_stays", ["booking_id"], unique=False)
    op.create_index(op.f("ix_bed_stays_hostel_id"), "bed_stays", ["hostel_id"], unique=False)
    op.create_index(op.f("ix_bed_stays_status"), "bed_stays", ["status"], unique=False)
    op.create_index(op.f("ix_bed_stays_student_id"), "bed_stays", ["student_id"], unique=False)

    op.create_table(
        "booking_status_history",
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("old_status", sa.Enum("DRAFT", "PAYMENT_PENDING", "PENDING_APPROVAL", "APPROVED", "REJECTED", "CHECKED_IN", "CHECKED_OUT", "CANCELLED", name="bookingstatus"), nullable=True),
        sa.Column("new_status", sa.Enum("DRAFT", "PAYMENT_PENDING", "PENDING_APPROVAL", "APPROVED", "REJECTED", "CHECKED_IN", "CHECKED_OUT", "CANCELLED", name="bookingstatus"), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_booking_status_history_booking_id"), "booking_status_history", ["booking_id"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refresh_tokens_token_hash"), "refresh_tokens", ["token_hash"], unique=True)
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)

    op.create_table(
        "otp_verifications",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("otp_code_hash", sa.String(length=255), nullable=False),
        sa.Column("otp_type", sa.Enum("REGISTRATION", "PASSWORD_RESET", name="otptype"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_otp_verifications_user_id"), "otp_verifications", ["user_id"], unique=False)

    op.create_table(
        "admin_hostel_mappings",
        sa.Column("admin_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_hostel_mappings_admin_id"), "admin_hostel_mappings", ["admin_id"], unique=False)
    op.create_index(op.f("ix_admin_hostel_mappings_hostel_id"), "admin_hostel_mappings", ["hostel_id"], unique=False)

    op.create_table(
        "supervisor_hostel_mappings",
        sa.Column("supervisor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supervisor_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_supervisor_hostel_mappings_hostel_id"), "supervisor_hostel_mappings", ["hostel_id"], unique=False)
    op.create_index(op.f("ix_supervisor_hostel_mappings_supervisor_id"), "supervisor_hostel_mappings", ["supervisor_id"], unique=False)

    op.create_table(
        "hostel_amenities",
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_hostel_amenities_hostel_id"), "hostel_amenities", ["hostel_id"], unique=False)

    op.create_table(
        "hostel_images",
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=500), nullable=False),
        sa.Column("caption", sa.String(length=255), nullable=True),
        sa.Column("image_type", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_hostel_images_hostel_id"), "hostel_images", ["hostel_id"], unique=False)

    op.create_table(
        "inquiries",
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_inquiries_hostel_id"), "inquiries", ["hostel_id"], unique=False)


def downgrade() -> None:
    for table in [
        "inquiries",
        "hostel_images",
        "hostel_amenities",
        "supervisor_hostel_mappings",
        "admin_hostel_mappings",
        "otp_verifications",
        "refresh_tokens",
        "booking_status_history",
        "bed_stays",
        "students",
        "bookings",
        "beds",
        "rooms",
        "hostels",
        "users",
    ]:
        op.drop_table(table)

    op.execute("DROP TYPE IF EXISTS bedstaystatus")
    op.execute("DROP TYPE IF EXISTS studentstatus")
    op.execute("DROP TYPE IF EXISTS bookingstatus")
    op.execute("DROP TYPE IF EXISTS bookingmode")
    op.execute("DROP TYPE IF EXISTS bedstatus")
    op.execute("DROP TYPE IF EXISTS roomtype")
    op.execute("DROP TYPE IF EXISTS hostelstatus")
    op.execute("DROP TYPE IF EXISTS hosteltype")
    op.execute("DROP TYPE IF EXISTS otptype")
    op.execute("DROP TYPE IF EXISTS userrole")
