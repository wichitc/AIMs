"""add reservation and stock transfer tables

Revision ID: 2c36e9611687
Revises: 12d5ce2228bd
Create Date: 2026-08-19 03:49:48.125760

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2c36e9611687'
down_revision: Union[str, None] = '12d5ce2228bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# NOTE: see 47c1c9181fb2's comment — autogenerate always proposes dropping ai-service's
# tables (separate alembic_version_ai chain, shared DB) and re-adding every existing
# table's use_alter=True FK constraints (reflection-order quirk). Both are stripped below;
# only the two genuinely new tables remain.


def upgrade() -> None:
    op.create_table('stock_transfer',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('material_id', sa.UUID(), nullable=False),
    sa.Column('source_location_id', sa.UUID(), nullable=False),
    sa.Column('destination_location_id', sa.UUID(), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('transfer_mode', sa.String(length=10), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('issue_document_id', sa.UUID(), nullable=True),
    sa.Column('receipt_document_id', sa.UUID(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['destination_location_id'], ['location.id'], ),
    sa.ForeignKeyConstraint(['issue_document_id'], ['material_document.id'], ),
    sa.ForeignKeyConstraint(['material_id'], ['material.id'], ),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['receipt_document_id'], ['material_document.id'], ),
    sa.ForeignKeyConstraint(['source_location_id'], ['location.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reservation',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('material_id', sa.UUID(), nullable=False),
    sa.Column('storage_location_id', sa.UUID(), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('issued_quantity', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('purpose', sa.String(length=300), nullable=True),
    sa.Column('maintenance_order_id', sa.UUID(), nullable=True),
    sa.Column('required_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['maintenance_order_id'], ['maintenance_order.id'], ),
    sa.ForeignKeyConstraint(['material_id'], ['material.id'], ),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['storage_location_id'], ['location.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('reservation')
    op.drop_table('stock_transfer')
