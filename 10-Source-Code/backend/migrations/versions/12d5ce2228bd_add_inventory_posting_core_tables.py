"""add inventory posting core tables

Revision ID: 12d5ce2228bd
Revises: cd3282989bb5
Create Date: 2026-08-18 12:25:21.807042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '12d5ce2228bd'
down_revision: Union[str, None] = 'cd3282989bb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# NOTE: see 47c1c9181fb2's comment — autogenerate noise stripped; only the four new tables.
# stock_balance/stock_ledger correctly lack created_by/updated_by (UUIDMixin only, no
# AuditMixin — the ledger is append-only and has no "creator" concept beyond the posting
# material_document, which is already audited).
# stock_ledger.occurred_at is timezone-aware (caught live: the model originally omitted
# DateTime(timezone=True), so asyncpg rejected inserting datetime.now(timezone.utc) against
# a naive TIMESTAMP column — fixed in the model and here before this migration was committed).


def upgrade() -> None:
    op.create_table('material_document',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('movement_type', sa.String(length=10), nullable=False),
    sa.Column('posted_date', sa.Date(), nullable=False),
    sa.Column('reference_type', sa.String(length=30), nullable=True),
    sa.Column('reference_id', sa.UUID(), nullable=True),
    sa.Column('reversal_of_id', sa.UUID(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['reversal_of_id'], ['material_document.id'], name='fk_material_document_reversal', use_alter=True),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('stock_balance',
    sa.Column('material_id', sa.UUID(), nullable=False),
    sa.Column('storage_location_id', sa.UUID(), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('value', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['material_id'], ['material.id'], ),
    sa.ForeignKeyConstraint(['storage_location_id'], ['location.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('material_id', 'storage_location_id', name='uq_stock_balance_dimension')
    )
    op.create_table('material_document_item',
    sa.Column('material_document_id', sa.UUID(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('material_id', sa.UUID(), nullable=False),
    sa.Column('storage_location_id', sa.UUID(), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('po_item_id', sa.UUID(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['material_document_id'], ['material_document.id'], ),
    sa.ForeignKeyConstraint(['material_id'], ['material.id'], ),
    sa.ForeignKeyConstraint(['po_item_id'], ['purchase_order_item.id'], ),
    sa.ForeignKeyConstraint(['storage_location_id'], ['location.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('stock_ledger',
    sa.Column('material_id', sa.UUID(), nullable=False),
    sa.Column('storage_location_id', sa.UUID(), nullable=False),
    sa.Column('signed_quantity', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('signed_value', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('material_document_item_id', sa.UUID(), nullable=False),
    sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['material_document_item_id'], ['material_document_item.id'], ),
    sa.ForeignKeyConstraint(['material_id'], ['material.id'], ),
    sa.ForeignKeyConstraint(['storage_location_id'], ['location.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('stock_ledger')
    op.drop_table('material_document_item')
    op.drop_table('stock_balance')
    op.drop_table('material_document')
