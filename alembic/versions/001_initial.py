"""Initial migration - create all tables

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "d40d7727d25c4ce7b6f5fd8d4ef0ff4a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "vehicles",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("customer_id", postgresql.UUID(), nullable=False),
        sa.Column("brand", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("plate", sa.String(20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plate"),
    )

    op.create_table(
        "service_orders",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("customer_id", postgresql.UUID(), nullable=False),
        sa.Column("vehicle_id", postgresql.UUID(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "service_items",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column(
            "service_order_id", postgresql.UUID(), nullable=False
        ),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["service_order_id"], ["service_orders.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "part_items",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column(
            "service_order_id", postgresql.UUID(), nullable=False
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["service_order_id"], ["service_orders.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("part_items")
    op.drop_table("service_items")
    op.drop_table("service_orders")
    op.drop_table("vehicles")
    op.drop_table("customers")
    op.drop_table("users")
