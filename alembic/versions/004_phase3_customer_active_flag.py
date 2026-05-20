"""phase 3 customer active flag

Revision ID: 004_phase3_customer_active_flag
Revises: 003_phase2_service_order_decision_fields
Create Date: 2026-05-19
"""

from alembic import op
import sqlalchemy as sa


revision = "cv9o42lluvw4rpmja99thtk3ln78x0g5"
down_revision = "f6e8f32cb5f74b299f9f89f39dc8ba02"
branch_labels = None
depends_on = None



def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.alter_column("customers", "is_active", server_default=None)



def downgrade() -> None:
    op.drop_column("customers", "is_active")
