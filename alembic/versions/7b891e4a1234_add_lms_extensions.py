"""add_lms_extensions

Revision ID: 7b891e4a1234
Revises: 5a55715b3274
Create Date: 2026-11-04 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b891e4a1234'
down_revision: Union[str, None] = '5a55715b3274'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add extra metadata columns to courses
    op.add_column('courses', sa.Column('category', sa.String(length=50), nullable=False, server_default='grammar'))
    op.add_column('courses', sa.Column('duration', sa.String(length=50), nullable=True, server_default='8 Weeks'))
    op.add_column('courses', sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('courses', sa.Column('tags', sa.JSON(), nullable=True, server_default='[]'))
    op.add_column('courses', sa.Column('resources', sa.JSON(), nullable=True, server_default='[]'))

    # 2. Instructor profiles
    op.create_table(
        'instructor_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('bio', sa.Text(), nullable=False),
        sa.Column('languages', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('experience_years', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('twitter', sa.String(length=255), nullable=True),
        sa.Column('linkedin', sa.String(length=255), nullable=True),
        sa.Column('youtube', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('upi_id', sa.String(length=100), nullable=True),
        sa.Column('bank_account', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_instructor_profile_user_id'),
    )
    op.create_index(op.f('ix_instructor_profiles_id'), 'instructor_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_instructor_profiles_user_id'), 'instructor_profiles', ['user_id'], unique=True)

    # 3. User streaks
    op.create_table(
        'user_streaks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('longest_streak', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_visit_date', sa.Date(), nullable=False, server_default=sa.text('CURRENT_DATE')),
        sa.Column('total_days_active', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('history', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_streaks_user_id'),
    )
    op.create_index(op.f('ix_user_streaks_id'), 'user_streaks', ['id'], unique=False)
    op.create_index(op.f('ix_user_streaks_user_id'), 'user_streaks', ['user_id'], unique=True)

    # 4. Articles
    op.create_table(
        'articles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('date_display', sa.String(length=50), nullable=False, server_default='Sep 2026'),
        sa.Column('read_time', sa.String(length=50), nullable=False, server_default='5 min read'),
        sa.Column('tag', sa.String(length=50), nullable=False, server_default='General'),
        sa.Column('color', sa.String(length=100), nullable=False, server_default='from-orange-500 to-red-500'),
        sa.Column('emoji', sa.String(length=20), nullable=False, server_default='📚'),
        sa.Column('author_name', sa.String(length=100), nullable=False, server_default='VartaLang Editorial'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_articles_slug'),
    )
    op.create_index(op.f('ix_articles_id'), 'articles', ['id'], unique=False)
    op.create_index(op.f('ix_articles_slug'), 'articles', ['slug'], unique=True)
    op.create_index(op.f('ix_articles_tag'), 'articles', ['tag'], unique=False)

    # 5. Job postings
    op.create_table(
        'job_postings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('team', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False, server_default='Full-time / Remote'),
        sa.Column('location', sa.String(length=100), nullable=False, server_default='Remote (India)'),
        sa.Column('emoji', sa.String(length=20), nullable=False, server_default='📚'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('requirements', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('apply_email', sa.String(length=255), nullable=False, server_default='support@cosmoindiaprakashan.in'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_job_postings_id'), 'job_postings', ['id'], unique=False)

    # 6. Job applications
    op.create_table(
        'job_applications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.String(length=100), nullable=True),
        sa.Column('applicant_name', sa.String(length=150), nullable=False),
        sa.Column('applicant_email', sa.String(length=255), nullable=False),
        sa.Column('resume_url', sa.String(length=500), nullable=True),
        sa.Column('cover_note', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='submitted'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_job_applications_id'), 'job_applications', ['id'], unique=False)

    # 7. Practice Labs
    op.create_table(
        'practice_labs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False, server_default='free'),
        sa.Column('duration', sa.String(length=50), nullable=False, server_default='10-15 min'),
        sa.Column('exercises', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('gradient', sa.String(length=100), nullable=False, server_default='from-blue-500 to-indigo-600'),
        sa.Column('highlights', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('eta', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_practice_labs_slug'),
    )
    op.create_index(op.f('ix_practice_labs_id'), 'practice_labs', ['id'], unique=False)
    op.create_index(op.f('ix_practice_labs_slug'), 'practice_labs', ['slug'], unique=True)

    # 8. Practice Sessions
    op.create_table(
        'practice_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('lab_id', sa.String(length=100), nullable=False),
        sa.Column('language', sa.String(length=50), nullable=False, server_default='Hindi'),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('accuracy_percentage', sa.Float(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practice_sessions_id'), 'practice_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_practice_sessions_lab_id'), 'practice_sessions', ['lab_id'], unique=False)
    op.create_index(op.f('ix_practice_sessions_user_id'), 'practice_sessions', ['user_id'], unique=False)

    # 9. Challenges
    op.create_table(
        'challenges',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('challenge_type', sa.String(length=50), nullable=False, server_default='daily_duel'),
        sa.Column('color', sa.String(length=100), nullable=False, server_default='from-red-500 to-orange-600'),
        sa.Column('eta', sa.String(length=50), nullable=False, server_default='Q4 2026'),
        sa.Column('xp_reward', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_challenges_slug'),
    )
    op.create_index(op.f('ix_challenges_id'), 'challenges', ['id'], unique=False)
    op.create_index(op.f('ix_challenges_slug'), 'challenges', ['slug'], unique=True)

    # 10. Challenge Leaderboard
    op.create_table(
        'challenge_leaderboard',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('user_name', sa.String(length=150), nullable=False),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('language', sa.String(length=50), nullable=False, server_default='Hindi'),
        sa.Column('xp', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rank', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_challenge_leaderboard_id'), 'challenge_leaderboard', ['id'], unique=False)
    op.create_index(op.f('ix_challenge_leaderboard_user_id'), 'challenge_leaderboard', ['user_id'], unique=False)

    # 11. Certifications
    op.create_table(
        'certifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('color', sa.String(length=100), nullable=False, server_default='from-amber-500 to-orange-600'),
        sa.Column('eta', sa.String(length=50), nullable=False, server_default='Q1 2027'),
        sa.Column('levels', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('requirements', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_certifications_slug'),
    )
    op.create_index(op.f('ix_certifications_id'), 'certifications', ['id'], unique=False)
    op.create_index(op.f('ix_certifications_slug'), 'certifications', ['slug'], unique=True)

    # 12. User Certifications
    op.create_table(
        'user_certifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('certificate_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('user_name', sa.String(length=150), nullable=False),
        sa.Column('certification_title', sa.String(length=150), nullable=False),
        sa.Column('language', sa.String(length=50), nullable=False, server_default='Hindi'),
        sa.Column('proficiency_level', sa.String(length=50), nullable=False, server_default='Beginner'),
        sa.Column('issue_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('verification_hash', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='valid'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('certificate_id', name='uq_user_certifications_certificate_id'),
    )
    op.create_index(op.f('ix_user_certifications_certificate_id'), 'user_certifications', ['certificate_id'], unique=True)
    op.create_index(op.f('ix_user_certifications_id'), 'user_certifications', ['id'], unique=False)
    op.create_index(op.f('ix_user_certifications_user_id'), 'user_certifications', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('user_certifications')
    op.drop_table('certifications')
    op.drop_table('challenge_leaderboard')
    op.drop_table('challenges')
    op.drop_table('practice_sessions')
    op.drop_table('practice_labs')
    op.drop_table('job_applications')
    op.drop_table('job_postings')
    op.drop_table('articles')
    op.drop_table('user_streaks')
    op.drop_table('instructor_profiles')
    op.drop_column('courses', 'resources')
    op.drop_column('courses', 'tags')
    op.drop_column('courses', 'is_featured')
    op.drop_column('courses', 'duration')
    op.drop_column('courses', 'category')

