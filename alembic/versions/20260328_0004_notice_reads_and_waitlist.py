"""notice_reads + waitlist_entries (J1 notice tracking, J5 waitlist)

Revision ID: 20260328_0004
Revises: 20260327_0003
Create Date: 2026-03-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260328_0004"
down_revision = "20260327_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    has_notice_reads = conn.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='notice_reads'")
    ).scalar()
    if not has_notice_reads:
        op.create_table(
            "notice_reads",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("notice_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["notice_id"], ["notices.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("notice_id", "user_id", name="uq_notice_read_notice_user"),
        )
        op.create_index("ix_notice_reads_notice_id", "notice_reads", ["notice_id"])
        op.create_index("ix_notice_reads_user_id", "notice_reads", ["user_id"])

    has_waitlist = conn.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='waitlist_entries'")
    ).scalar()
    if not has_waitlist:
        waitlist_status = postgresql.ENUM(
            "ACTIVE",
            "NOTIFIED",
            "CONVERTED",
            "CANCELLED",
            name="waitliststatus",
            create_type=True,
        )
        waitlist_status.create(conn, checkfirst=True)

        booking_mode_enum = postgresql.ENUM(
            "DAILY",
            "MONTHLY",
            name="bookingmode",
            create_type=False,
        )

        op.create_table(
            "waitlist_entries",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("visitor_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("hostel_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("bed_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("check_in_date", sa.Date(), nullable=False),
            sa.Column("check_out_date", sa.Date(), nullable=False),
            sa.Column("booking_mode", booking_mode_enum, nullable=False),
            sa.Column(
                "status",
                postgresql.ENUM(
                    "ACTIVE",
                    "NOTIFIED",
                    "CONVERTED",
                    "CANCELLED",
                    name="waitliststatus",
                    create_type=False,
                ),
                nullable=False,
                server_default=sa.text("'ACTIVE'::waitliststatus"),
            ),
            sa.Column("notified_at", sa.Date(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["visitor_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["hostel_id"], ["hostels.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
            sa.ForeignKeyConstraint(["bed_id"], ["beds.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_waitlist_entries_visitor_id", "waitlist_entries", ["visitor_id"])
        op.create_index("ix_waitlist_entries_hostel_id", "waitlist_entries", ["hostel_id"])
        op.create_index("ix_waitlist_entries_room_id", "waitlist_entries", ["room_id"])
        op.create_index("ix_waitlist_entries_bed_id", "waitlist_entries", ["bed_id"])


def downgrade() -> None:
    op.drop_index("ix_waitlist_entries_bed_id", table_name="waitlist_entries")
    op.drop_index("ix_waitlist_entries_room_id", table_name="waitlist_entries")
    op.drop_index("ix_waitlist_entries_hostel_id", table_name="waitlist_entries")
    op.drop_index("ix_waitlist_entries_visitor_id", table_name="waitlist_entries")
    op.drop_table("waitlist_entries")
    op.execute("DROP TYPE IF EXISTS waitliststatus")

    op.drop_index("ix_notice_reads_user_id", table_name="notice_reads")
    op.drop_index("ix_notice_reads_notice_id", table_name="notice_reads")
    op.drop_table("notice_reads")
