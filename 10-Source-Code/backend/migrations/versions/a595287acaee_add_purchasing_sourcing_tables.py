"""add purchasing sourcing tables

Revision ID: a595287acaee
Revises: 47c1c9181fb2
Create Date: 2026-08-14 05:13:03.666843

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a595287acaee'
down_revision: Union[str, None] = '47c1c9181fb2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# NOTE: see 47c1c9181fb2's comment — autogenerate noise (ai-service's tables, spurious
# use_alter FK re-adds on every existing table) was stripped; this migration contains only
# the three new sourcing tables.


def upgrade() -> None:
    op.create_table('purchasing_info_record',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('material_id', sa.UUID(), nullable=False),
    sa.Column('supplier_id', sa.UUID(), nullable=False),
    sa.Column('price', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('lead_time_days', sa.Integer(), nullable=True),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['material_id'], ['material.id'], ),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('quota_arrangement',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('material_id', sa.UUID(), nullable=False),
    sa.Column('supplier_id', sa.UUID(), nullable=False),
    sa.Column('quota_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['material_id'], ['material.id'], ),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('source_list_entry',
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('material_id', sa.UUID(), nullable=False),
    sa.Column('supplier_id', sa.UUID(), nullable=False),
    sa.Column('is_fixed', sa.Boolean(), nullable=False),
    sa.Column('is_blocked', sa.Boolean(), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_to', sa.Date(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('updated_by', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_created_by_user', use_alter=True),
    sa.ForeignKeyConstraint(['material_id'], ['material.id'], ),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], name='fk_updated_by_user', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('source_list_entry')
    op.drop_table('quota_arrangement')
    op.drop_table('purchasing_info_record')
