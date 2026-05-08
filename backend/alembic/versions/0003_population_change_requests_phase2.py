"""population change requests — phase 2

Revision ID: 0003_population_change_requests_phase2
Revises: 0002_population_registry
Create Date: 2026-05-08 22:30:00

Adds the unified review/approve fields and the new statuses & types required
by Phase-2 of the population module:

* `request_number` — unique tracking number.
* `reviewed_by_user_id`, `reviewed_at`, `review_notes`
* `approved_by_user_id`, `approved_at`
* `rejection_reason`
* New enum values for `ChangeRequestStatus`: `draft`, `under_review`,
  `cancelled`. Legacy `mukhtar_review` / `municipality_review` are kept.
* New enum value for `ChangeRequestType`: `move_member`.

On SQLite enums are stored as TEXT, so adding values is transparent. On
PostgreSQL the enum types are ALTERed in a backend-agnostic way.
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_population_change_requests_phase2"
down_revision = "0002_population_registry"
branch_labels = None
depends_on = None


new_status_values = ("draft", "under_review", "cancelled")
new_type_values = ("move_member",)


def upgrade() -> None:
    bind = op.get_bind()

    # Extend enums on PostgreSQL. SQLite stores enums as TEXT so nothing
    # needs to be done there.
    if bind.dialect.name == "postgresql":
        for value in new_status_values:
            op.execute(
                f"ALTER TYPE changerequeststatus ADD VALUE IF NOT EXISTS '{value}'"
            )
        for value in new_type_values:
            op.execute(
                f"ALTER TYPE changerequesttype ADD VALUE IF NOT EXISTS '{value}'"
            )

    with op.batch_alter_table("population_change_requests") as batch:
        batch.add_column(sa.Column("request_number", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("review_notes", sa.Text(), nullable=True))
        batch.add_column(sa.Column("approved_by_user_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("rejection_reason", sa.Text(), nullable=True))
        batch.create_foreign_key(
            "fk_pcr_reviewed_by_user_id",
            "users",
            ["reviewed_by_user_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_pcr_approved_by_user_id",
            "users",
            ["approved_by_user_id"],
            ["id"],
        )
        batch.create_index(
            "ix_population_change_requests_request_number",
            ["request_number"],
            unique=True,
        )
        batch.create_index(
            "ix_population_change_requests_reviewed_by_user_id",
            ["reviewed_by_user_id"],
            unique=False,
        )
        batch.create_index(
            "ix_population_change_requests_approved_by_user_id",
            ["approved_by_user_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("population_change_requests") as batch:
        batch.drop_index("ix_population_change_requests_approved_by_user_id")
        batch.drop_index("ix_population_change_requests_reviewed_by_user_id")
        batch.drop_index("ix_population_change_requests_request_number")
        batch.drop_constraint("fk_pcr_approved_by_user_id", type_="foreignkey")
        batch.drop_constraint("fk_pcr_reviewed_by_user_id", type_="foreignkey")
        batch.drop_column("rejection_reason")
        batch.drop_column("approved_at")
        batch.drop_column("approved_by_user_id")
        batch.drop_column("review_notes")
        batch.drop_column("reviewed_at")
        batch.drop_column("reviewed_by_user_id")
        batch.drop_column("request_number")
    # Note: PostgreSQL enum values cannot be removed without re-creating the
    # type. Left in place — they are harmless if unused.
