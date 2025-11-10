"""Drop unused table syndicate_config.

Revision ID: dc12aa918b85
Revises: f2304c5669f5
Create Date: 2025-11-10 13:21:53.460708
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "dc12aa918b85"
down_revision = "f2304c5669f5"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("syndicate_config")


def downgrade():
    op.create_table(
        "syndicate_config",
        sa.Column("id", sa.UnicodeText, primary_key=True),
        sa.Column("syndicate_url", sa.UnicodeText, unique=True),
        sa.Column("syndicate_api_key", sa.UnicodeText),
        sa.Column("syndicate_organization", sa.UnicodeText),
        sa.Column("syndicate_replicate_organization", sa.Boolean),
        sa.Column("syndicate_author", sa.UnicodeText),
        sa.Column("predicate", sa.UnicodeText),
        sa.Column("syndicate_field_id", sa.UnicodeText),
        sa.Column("syndicate_flag", sa.UnicodeText),
        sa.Column("syndicate_prefix", sa.UnicodeText),
    )
