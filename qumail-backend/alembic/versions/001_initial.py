"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2025-10-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create oauth_tokens table
    op.create_table('oauth_tokens',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('encrypted_access_token', sa.Text(), nullable=False),
        sa.Column('encrypted_refresh_token', sa.Text(), nullable=True),
        sa.Column('token_type', sa.String(50), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scopes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oauth_tokens_user_email'), 'oauth_tokens', ['user_email'])

    # Create security_audit_logs table
    op.create_table('security_audit_logs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_security_audit_logs_event_type'), 'security_audit_logs', ['event_type'])
    op.create_index(op.f('ix_security_audit_logs_user_id'), 'security_audit_logs', ['user_id'])
    op.create_index(op.f('ix_security_audit_logs_timestamp'), 'security_audit_logs', ['timestamp'])

    # Create encryption_sessions table
    op.create_table('encryption_sessions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('security_level', sa.Integer(), nullable=False),
        sa.Column('algorithm', sa.String(100), nullable=False),
        sa.Column('km1_key_id', sa.String(255), nullable=True),
        sa.Column('km2_key_id', sa.String(255), nullable=True),
        sa.Column('operation', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_encryption_sessions_session_id'), 'encryption_sessions', ['session_id'], unique=True)
    op.create_index(op.f('ix_encryption_sessions_user_email'), 'encryption_sessions', ['user_email'])

    # Create email_messages table
    op.create_table('email_messages',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('message_id', sa.String(255), nullable=False),
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('sender', sa.String(255), nullable=False),
        sa.Column('recipient', sa.String(255), nullable=False),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('security_level', sa.Integer(), nullable=False),
        sa.Column('encryption_algorithm', sa.String(100), nullable=False),
        sa.Column('encryption_session_id', sa.String(255), nullable=False),
        sa.Column('gmail_message_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_messages_message_id'), 'email_messages', ['message_id'], unique=True)
    op.create_index(op.f('ix_email_messages_user_email'), 'email_messages', ['user_email'])

    # Create km_server_status table
    op.create_table('km_server_status',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('server_name', sa.String(50), nullable=False),
        sa.Column('server_url', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('last_check', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('available_keys', sa.Integer(), nullable=True),
        sa.Column('max_key_size', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create system_health table
    op.create_table('system_health',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('component', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('last_check', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('system_health')
    op.drop_table('km_server_status')
    op.drop_table('email_messages')
    op.drop_table('encryption_sessions')
    op.drop_table('security_audit_logs')
    op.drop_table('oauth_tokens')
    op.drop_table('users')