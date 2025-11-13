"""Add syndication_log table.

Revision ID: b1c3e920f499
Revises: dc12aa918b85
Create Date: 2025-11-11 16:57:52.264578
"""

from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

import ckan.plugins.toolkit as tk

from ckanext.syndicate import model, utils

# revision identifiers, used by Alembic.
revision = "b1c3e920f499"
down_revision = "dc12aa918b85"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "syndication_log",
        sa.Column("local_id", sa.String(length=255), nullable=False),
        sa.Column("target_id", sa.String(length=255), nullable=False),
        sa.Column("profile_id", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=50), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["local_id"],
            ["package.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("target_id", "profile_id"),
    )

    op.create_index(
        "ix_syndication_log_local_profile",
        "syndication_log",
        ["local_id", "profile_id"],
    )

    migrate_records_from_extras()


def downgrade():
    op.drop_index("ix_syndication_log_local_profile", table_name="syndication_log")
    op.drop_table("syndication_log")


def migrate_records_from_extras() -> None:
    """Migrate existing syndication records from package extras to the new table.

    Previously, we stored syndication target IDs in package extras under
    the field_id defined in each profile. Now we have a dedicated syndication_log
    table, so we need to migrate existing records there.
    """
    conn = op.get_bind()
    profiles = utils.get_profiles()
    syndication_log = sa.table(
        "syndication_log",
        sa.column("local_id", sa.String),
        sa.column("target_id", sa.String),
        sa.column("profile_id", sa.String),
        sa.column("state", sa.String),
        sa.column("error", sa.Text),
        sa.column("timestamp", sa.DateTime(timezone=True)),
    )

    for profile in profiles:
        start = 0
        offset = 1000

        while True:
            packages = tk.get_action("package_search")(
                {"ignore_auth": True},
                {
                    "fq": f"extras_{profile.field_id}:*",
                    "fl": f"extras_{profile.field_id},id",
                    "rows": offset,
                    "start": start,
                },
            )["results"]

            if not packages:
                break

            start += offset

            rows = []

            for package in packages:
                if profile.field_id not in package:
                    continue

                rows.append(
                    {
                        "local_id": package["id"],
                        "target_id": package[profile.field_id],
                        "profile_id": profile.id,
                        "state": model.SyndicationLog.State.SYNCED,
                        "error": None,
                        "timestamp": datetime.now(timezone.utc),
                    }
                )

            if rows:
                conn.execute(syndication_log.insert(), rows)
