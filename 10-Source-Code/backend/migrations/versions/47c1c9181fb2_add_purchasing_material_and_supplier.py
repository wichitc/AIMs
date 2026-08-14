"""add purchasing material and supplier

Revision ID: 47c1c9181fb2
Revises: b6027a2fc5d4
Create Date: 2026-08-14 04:54:54.138612

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '47c1c9181fb2'
down_revision: Union[str, None] = 'b6027a2fc5d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# NOTE: autogenerate also proposed dropping ai-service's tables (alembic_version_ai,
# ai_prediction, document_embedding — it owns a separate migration chain against the same
# physical database, see migrations/env.py's VERSION_TABLE comment) and re-creating every
# existing table's use_alter=True created_by/updated_by FKs (a reflection-order quirk, not a
# real schema gap — those constraints already exist). Both were stripped from this migration;
# it contains only the two new tables.


def upgrade() -> None:
    op.create_table('material',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('material_number', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('material_type', sa.String(length=30), nullable=False),
    sa.Column('material_group', sa.String(length=100), nullable=True),
    sa.Column('base_uom', sa.String(length=10), nullable=False),
    sa.Column('moving_average_price', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('min_stock_level', sa.Numeric(precision=14, scale=3), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('org_id', 'material_number', name='uq_material_org_number')
    )
    op.create_table('supplier',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('supplier_number', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('tax_id', sa.String(length=50), nullable=True),
    sa.Column('country', sa.String(length=100), nullable=True),
    sa.Column('email', sa.String(length=200), nullable=True),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('address', sa.String(), nullable=True),
    sa.Column('payment_terms', sa.String(length=100), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_blocked', sa.Boolean(), nullable=False),
    sa.Column('block_reason', sa.String(length=300), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('org_id', 'supplier_number', name='uq_supplier_org_number')
    )


def downgrade() -> None:
    op.drop_table('supplier')
    op.drop_table('material')
