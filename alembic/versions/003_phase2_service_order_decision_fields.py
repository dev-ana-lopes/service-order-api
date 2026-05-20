"""Phase 2 adjustments for service-order decision tracking

Revision ID: 003_phase2_service_order_decision_fields
Revises: 002_phase1_catalog_and_fields
Create Date: 2026-03-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "f6e8f32cb5f74b299f9f89f39dc8ba02"
down_revision = "55ff6e9305214157b1bfd6b7ef6f0f1b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "service_orders",
        sa.Column("approval_decision", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "service_orders",
        sa.Column("approval_decision_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "service_orders",
        sa.Column("rejection_reason", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("service_orders", "rejection_reason")
    op.drop_column("service_orders", "approval_decision_at")
    op.drop_column("service_orders", "approval_decision")
