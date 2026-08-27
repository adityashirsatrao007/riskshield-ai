"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-27
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transaction_id", sa.String(32), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(3), server_default="INR"),
        sa.Column("merchant_id", sa.String(16), nullable=False),
        sa.Column("customer_id", sa.String(16), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("card_type", sa.String(16), nullable=True),
        sa.Column("is_international", sa.Boolean(), server_default="0"),
        sa.Column("risk_score", sa.Float(), server_default="0.0"),
        sa.Column("risk_level", sa.String(16), server_default="low"),
        sa.Column("is_flagged", sa.Boolean(), server_default="0"),
        sa.Column("is_resolved", sa.Boolean(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transactions_transaction_id", "transactions", ["transaction_id"], unique=True)
    op.create_index("ix_transactions_merchant_id", "transactions", ["merchant_id"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(16), nullable=False),
        sa.Column("explanation", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(16), server_default="open"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_status", "alerts", ["status"])

    op.create_table(
        "audit_trails",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("model_version", sa.String(16), nullable=True),
        sa.Column("processing_time_ms", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "merchant_stats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("merchant_id", sa.String(16), nullable=False),
        sa.Column("total_transactions", sa.Integer(), server_default="0"),
        sa.Column("flagged_count", sa.Integer(), server_default="0"),
        sa.Column("resolved_count", sa.Integer(), server_default="0"),
        sa.Column("total_potential_savings", sa.Float(), server_default="0.0"),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id"),
    )

    op.create_table(
        "merchants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("api_key", sa.String(64), nullable=False),
        sa.Column("api_key_hash", sa.String(128), nullable=False),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.Column("rate_limit", sa.Integer(), server_default="120"),
        sa.Column("tier", sa.String(16), server_default="free"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("last_active", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_merchants_api_key", "merchants", ["api_key"], unique=True)


def downgrade() -> None:
    op.drop_table("merchants")
    op.drop_table("merchant_stats")
    op.drop_table("audit_trails")
    op.drop_table("alerts")
    op.drop_table("transactions")
