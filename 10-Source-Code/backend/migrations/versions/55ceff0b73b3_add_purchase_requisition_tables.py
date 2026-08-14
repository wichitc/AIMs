"""add purchase requisition tables

Revision ID: 55ceff0b73b3
Revises: a595287acaee
Create Date: 2026-08-14 09:13:46.769338

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '55ceff0b73b3'
down_revision: Union[str, None] = 'a595287acaee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# NOTE: see 47c1c9181fb2's comment — autogenerate noise stripped; only the two new tables.


def upgrade() -> None:
    op.create_table('purchase_requisition',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('requester_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('requested_date', sa.Date(), nullable=False),
    sa.Column('required_date', sa.Date(), nullable=True),
    sa.Column('maintenance_order_id', sa.UUID(), nullable=True),
    sa.Column('defect_id', sa.UUID(), nullable=True),
    sa.Column('decision_by', sa.UUID(), nullable=True),
    sa.Column('decision_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('decision_reason', sa.String(length=500), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['decision_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['defect_id'], ['defect.id'], ),
    sa.ForeignKeyConstraint(['maintenance_order_id'], ['maintenance_order.id'], ),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['requester_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('purchase_requisition_item',
    sa.Column('purchase_requisition_id', sa.UUID(), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('material_id', sa.UUID(), nullable=False),
    sa.Column('quantity', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('estimated_price', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('required_date', sa.Date(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['material_id'], ['material.id'], ),
    sa.ForeignKeyConstraint(['purchase_requisition_id'], ['purchase_requisition.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('purchase_requisition_item')
    op.drop_table('purchase_requisition')
