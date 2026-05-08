"""population registry schema

Revision ID: 0002_population_registry
Revises: 0001_initial
Create Date: 2026-05-08 21:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_population_registry"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


# Note: SQLite has no native ENUM. The original 0001 migration declared the
# `userrole` enum but on SQLite it is stored as TEXT, so adding new values is
# transparent. On PostgreSQL the enum type would need to be ALTERed; that is
# handled below in a backend-agnostic way.

new_user_roles = ("super_admin", "governor", "municipality_chief", "mukhtar", "household_head")

gender_enum = sa.Enum("male", "female", name="gender")
life_status_enum = sa.Enum("alive", "deceased", name="lifestatus")
relation_enum = sa.Enum(
    "self", "spouse", "child", "parent", "sibling", "other", name="relationtohead"
)
verification_enum = sa.Enum("pending", "verified", "rejected", name="householdverificationstatus")
change_request_type_enum = sa.Enum(
    "birth", "death", "address_change", "correction", "add_member", "remove_member",
    name="changerequesttype",
)
change_request_status_enum = sa.Enum(
    "submitted", "mukhtar_review", "municipality_review", "approved", "rejected",
    name="changerequeststatus",
)


def upgrade() -> None:
    bind = op.get_bind()

    # Extend userrole enum on PostgreSQL.
    if bind.dialect.name == "postgresql":
        for value in new_user_roles:
            op.execute(f"ALTER TYPE userrole ADD VALUE IF NOT EXISTS '{value}'")

    # Administrative scope tables ------------------------------------------------
    op.create_table(
        "governorates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name_ar", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_governorates_id"), "governorates", ["id"], unique=False)

    op.create_table(
        "municipalities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("governorate_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name_ar", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["governorate_id"], ["governorates.id"]),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_municipalities_id"), "municipalities", ["id"], unique=False)
    op.create_index(op.f("ix_municipalities_governorate_id"), "municipalities", ["governorate_id"], unique=False)

    op.create_table(
        "districts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("municipality_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name_ar", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["municipality_id"], ["municipalities.id"]),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_districts_id"), "districts", ["id"], unique=False)
    op.create_index(op.f("ix_districts_municipality_id"), "districts", ["municipality_id"], unique=False)

    op.create_table(
        "neighborhoods",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("district_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name_ar", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_neighborhoods_id"), "neighborhoods", ["id"], unique=False)
    op.create_index(op.f("ix_neighborhoods_district_id"), "neighborhoods", ["district_id"], unique=False)

    # User scope columns --------------------------------------------------------
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("governorate_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("municipality_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("district_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("neighborhood_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("national_id", sa.String(length=64), nullable=True))
        batch.create_foreign_key("fk_users_governorate_id", "governorates", ["governorate_id"], ["id"])
        batch.create_foreign_key("fk_users_municipality_id", "municipalities", ["municipality_id"], ["id"])
        batch.create_foreign_key("fk_users_district_id", "districts", ["district_id"], ["id"])
        batch.create_foreign_key("fk_users_neighborhood_id", "neighborhoods", ["neighborhood_id"], ["id"])
        batch.create_index("ix_users_governorate_id", ["governorate_id"], unique=False)
        batch.create_index("ix_users_municipality_id", ["municipality_id"], unique=False)
        batch.create_index("ix_users_district_id", ["district_id"], unique=False)
        batch.create_index("ix_users_neighborhood_id", ["neighborhood_id"], unique=False)
        batch.create_index("ix_users_national_id", ["national_id"], unique=False)

    # Households (head_person_id is added later as ALTER because of cyclic FK).
    op.create_table(
        "households",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("head_person_id", sa.Integer(), nullable=True),
        sa.Column("head_user_id", sa.Integer(), nullable=True),
        sa.Column("address_line", sa.String(length=255), nullable=False),
        sa.Column("governorate_id", sa.Integer(), nullable=False),
        sa.Column("municipality_id", sa.Integer(), nullable=False),
        sa.Column("district_id", sa.Integer(), nullable=False),
        sa.Column("neighborhood_id", sa.Integer(), nullable=True),
        sa.Column("assigned_mukhtar_user_id", sa.Integer(), nullable=True),
        sa.Column("verification_status", verification_enum, nullable=False),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["head_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["governorate_id"], ["governorates.id"]),
        sa.ForeignKeyConstraint(["municipality_id"], ["municipalities.id"]),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"]),
        sa.ForeignKeyConstraint(["neighborhood_id"], ["neighborhoods.id"]),
        sa.ForeignKeyConstraint(["assigned_mukhtar_user_id"], ["users.id"]),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_households_id"), "households", ["id"], unique=False)
    op.create_index(op.f("ix_households_code"), "households", ["code"], unique=True)
    op.create_index(op.f("ix_households_head_user_id"), "households", ["head_user_id"], unique=False)
    op.create_index(op.f("ix_households_governorate_id"), "households", ["governorate_id"], unique=False)
    op.create_index(op.f("ix_households_municipality_id"), "households", ["municipality_id"], unique=False)
    op.create_index(op.f("ix_households_district_id"), "households", ["district_id"], unique=False)
    op.create_index(op.f("ix_households_neighborhood_id"), "households", ["neighborhood_id"], unique=False)
    op.create_index(op.f("ix_households_assigned_mukhtar_user_id"), "households", ["assigned_mukhtar_user_id"], unique=False)
    op.create_index(op.f("ix_households_verification_status"), "households", ["verification_status"], unique=False)

    # Persons -------------------------------------------------------------------
    op.create_table(
        "persons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("gender", gender_enum, nullable=False),
        sa.Column("relation_to_head", relation_enum, nullable=False),
        sa.Column("life_status", life_status_enum, nullable=False),
        sa.Column("death_date", sa.Date(), nullable=True),
        sa.Column("national_id", sa.String(length=64), nullable=True),
        sa.Column("digital_identity_ref", sa.String(length=128), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"]),
    )
    op.create_index(op.f("ix_persons_id"), "persons", ["id"], unique=False)
    op.create_index(op.f("ix_persons_household_id"), "persons", ["household_id"], unique=False)
    op.create_index(op.f("ix_persons_national_id"), "persons", ["national_id"], unique=False)
    op.create_index(op.f("ix_persons_life_status"), "persons", ["life_status"], unique=False)
    op.create_index(op.f("ix_persons_is_archived"), "persons", ["is_archived"], unique=False)

    # Cyclic FK households.head_person_id → persons.id
    if bind.dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_household_head_person", "households", "persons", ["head_person_id"], ["id"]
        )

    # Population change requests -----------------------------------------------
    op.create_table(
        "population_change_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_type", change_request_type_enum, nullable=False),
        sa.Column("status", change_request_status_enum, nullable=False),
        sa.Column("submitted_by_user_id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("target_person_id", sa.Integer(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("mukhtar_user_id", sa.Integer(), nullable=True),
        sa.Column("mukhtar_decision_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mukhtar_comment", sa.Text(), nullable=True),
        sa.Column("municipality_user_id", sa.Integer(), nullable=True),
        sa.Column("municipality_decision_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("municipality_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["submitted_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"]),
        sa.ForeignKeyConstraint(["target_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["mukhtar_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["municipality_user_id"], ["users.id"]),
    )
    op.create_index(op.f("ix_population_change_requests_id"), "population_change_requests", ["id"], unique=False)
    op.create_index(op.f("ix_population_change_requests_request_type"), "population_change_requests", ["request_type"], unique=False)
    op.create_index(op.f("ix_population_change_requests_status"), "population_change_requests", ["status"], unique=False)
    op.create_index(op.f("ix_population_change_requests_submitted_by_user_id"), "population_change_requests", ["submitted_by_user_id"], unique=False)
    op.create_index(op.f("ix_population_change_requests_household_id"), "population_change_requests", ["household_id"], unique=False)
    op.create_index(op.f("ix_population_change_requests_target_person_id"), "population_change_requests", ["target_person_id"], unique=False)

    # Population event log -----------------------------------------------------
    op.create_table(
        "population_event_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=True),
        sa.Column("person_id", sa.Integer(), nullable=True),
        sa.Column("change_request_id", sa.Integer(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["change_request_id"], ["population_change_requests.id"]),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
    )
    op.create_index(op.f("ix_population_event_logs_id"), "population_event_logs", ["id"], unique=False)
    op.create_index(op.f("ix_population_event_logs_event_type"), "population_event_logs", ["event_type"], unique=False)
    op.create_index(op.f("ix_population_event_logs_household_id"), "population_event_logs", ["household_id"], unique=False)
    op.create_index(op.f("ix_population_event_logs_person_id"), "population_event_logs", ["person_id"], unique=False)
    op.create_index(op.f("ix_population_event_logs_change_request_id"), "population_event_logs", ["change_request_id"], unique=False)
    op.create_index(op.f("ix_population_event_logs_actor_user_id"), "population_event_logs", ["actor_user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("population_event_logs")
    op.drop_table("population_change_requests")

    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.drop_constraint("fk_household_head_person", "households", type_="foreignkey")

    op.drop_table("persons")
    op.drop_table("households")

    with op.batch_alter_table("users") as batch:
        batch.drop_index("ix_users_national_id")
        batch.drop_index("ix_users_neighborhood_id")
        batch.drop_index("ix_users_district_id")
        batch.drop_index("ix_users_municipality_id")
        batch.drop_index("ix_users_governorate_id")
        batch.drop_constraint("fk_users_neighborhood_id", type_="foreignkey")
        batch.drop_constraint("fk_users_district_id", type_="foreignkey")
        batch.drop_constraint("fk_users_municipality_id", type_="foreignkey")
        batch.drop_constraint("fk_users_governorate_id", type_="foreignkey")
        batch.drop_column("national_id")
        batch.drop_column("neighborhood_id")
        batch.drop_column("district_id")
        batch.drop_column("municipality_id")
        batch.drop_column("governorate_id")

    op.drop_table("neighborhoods")
    op.drop_table("districts")
    op.drop_table("municipalities")
    op.drop_table("governorates")

    for enum in (
        change_request_status_enum,
        change_request_type_enum,
        verification_enum,
        relation_enum,
        life_status_enum,
        gender_enum,
    ):
        enum.drop(op.get_bind(), checkfirst=True)
