"""add rfq quotation purchase order tables

Revision ID: cd3282989bb5
Revises: 55ceff0b73b3
Create Date: 2026-08-18 12:09:31.909213

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cd3282989bb5'
down_revision: Union[str, None] = '55ceff0b73b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# NOTE: see 47c1c9181fb2's comment — autogenerate noise stripped; only the six new tables.


def upgrade() -> None:
    op.create_table('rfq',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('purchase_requisition_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('deadline', sa.Date(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['purchase_requisition_id'], ['purchase_requisition.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('purchase_order',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('supplier_id', sa.UUID(), nullable=False),
    sa.Column('purchase_requisition_id', sa.UUID(), nullable=True),
    sa.Column('rfq_id', sa.UUID(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('order_date', sa.Date(), nullable=False),
    sa.Column('approved_by', sa.UUID(), nullable=True),
    sa.Column('confirmed_date', sa.Date(), nullable=True),
    sa.Column('confirmed_by_supplier', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['approved_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['purchase_requisition_id'], ['purchase_requisition.id'], ),
    sa.ForeignKeyConstraint(['rfq_id'], ['rfq.id'], ),
    sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('quotation',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('rfq_id', sa.UUID(), nullable=False),
    sa.Column('supplier_id', sa.UUID(), nullable=False),
    sa.Column('submitted_date', sa.Date(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['rfq_id'], ['rfq.id'], ),
    sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('rfq_supplier_invite',
    sa.Column('rfq_id', sa.UUID(), nullable=False),
    sa.Column('supplier_id', sa.UUID(), nullable=False),
    sa.Column('dispatched_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['rfq_id'], ['rfq.id'], ),
    sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('rfq_id', 'supplier_id', name='uq_rfq_supplier_invite')
    )
    op.create_table('purchase_order_item',
    sa.Column('purchase_order_id', sa.UUID(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('material_id', sa.UUID(), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('received_quantity', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('pr_item_id', sa.UUID(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['material_id'], ['material.id'], ),
    sa.ForeignKeyConstraint(['pr_item_id'], ['purchase_requisition_item.id'], ),
    sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_order.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('quotation_item',
    sa.Column('quotation_id', sa.UUID(), nullable=False),
    sa.Column('pr_item_id', sa.UUID(), nullable=False),
    sa.Column('material_id', sa.UUID(), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('is_awarded', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['material_id'], ['material.id'], ),
    sa.ForeignKeyConstraint(['pr_item_id'], ['purchase_requisition_item.id'], ),
    sa.ForeignKeyConstraint(['quotation_id'], ['quotation.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('quotation_item')
    op.drop_table('purchase_order_item')
    op.drop_table('rfq_supplier_invite')
    op.drop_table('quotation')
    op.drop_table('purchase_order')
    op.drop_table('rfq')
