"""Add recording_comments and recording_comment_edits tables

Revision ID: 017_recording_comments
Revises: 016_allowed_domains
Create Date: 2026-11-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = '017_recording_comments'
down_revision = '016_allowed_domains'
branch_labels = None
depends_on = None


def upgrade():
    comment_type = sa.Enum('bug', 'issue', 'improvement', name='commenttype')
    comment_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'recording_comments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('recording_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('type', comment_type, nullable=False),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('anchor_sequence', sa.Integer, nullable=True),
        sa.Column('anchor_timestamp', sa.DateTime, nullable=True),
        sa.Column('anchor_url', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_recording_comments_session_id', 'recording_comments', ['session_id'])
    op.create_index('ix_recording_comments_user_id', 'recording_comments', ['user_id'])

    op.create_table(
        'recording_comment_edits',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('comment_id', UUID(as_uuid=True), sa.ForeignKey('recording_comments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('editor_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('previous_text', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_recording_comment_edits_comment_id', 'recording_comment_edits', ['comment_id'])


def downgrade():
    op.drop_index('ix_recording_comment_edits_comment_id', 'recording_comment_edits')
    op.drop_table('recording_comment_edits')
    op.drop_index('ix_recording_comments_user_id', 'recording_comments')
    op.drop_index('ix_recording_comments_session_id', 'recording_comments')
    op.drop_table('recording_comments')
    sa.Enum(name='commenttype').drop(op.get_bind(), checkfirst=True)
