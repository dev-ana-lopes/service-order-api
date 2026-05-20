"""Phase 1 additions: CPF/CNPJ, catalog, inventory, service order timing

Revision ID: 002_phase1_catalog_and_fields
Revises: 001_initial
Create Date: 2026-03-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "55ff6e9305214157b1bfd6b7ef6f0f1b"
down_revision = "d40d7727d25c4ce7b6f5fd8d4ef0ff4a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("cpf_cnpj", sa.String(14), nullable=True))
    op.create_unique_constraint("uq_customers_cpf_cnpj", "customers", ["cpf_cnpj"])

    op.add_column("service_orders", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column(
        "service_orders", sa.Column("finished_at", sa.DateTime(), nullable=True)
    )

    op.create_table(
        "catalog_services",
        sa.Column("id", sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("description"),
    )

    op.create_table(
        "inventory_parts",
        sa.Column("id", sa.dialects.postgresql.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )


def downgrade() -> None:
    op.drop_table("inventory_parts")
    op.drop_table("catalog_services")
    op.drop_column("service_orders", "finished_at")
    op.drop_column("service_orders", "started_at")
    op.drop_constraint("uq_customers_cpf_cnpj", "customers", type_="unique")
    op.drop_column("customers", "cpf_cnpj")
