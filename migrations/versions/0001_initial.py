"""initial schema"""
from alembic import op
import sqlalchemy as sa
import uuid

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def create_base_columns():
    return [
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted", sa.Boolean(), nullable=False, default=False),
    ]

def upgrade():
    # business
    op.create_table(
        "business",
        *create_base_columns(),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country", sa.String(64), nullable=False),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.UniqueConstraint("name", "country", name="uq_business_name_country"),
    )
    # businessuser
    op.create_table(
        "businessuser",
        *create_base_columns(),
        sa.Column("business_id", sa.UUID(as_uuid=True), sa.ForeignKey("business.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
    )
    # person
    op.create_table(
        "person",
        *create_base_columns(),
        sa.Column("phone_hash", sa.String(128), nullable=False),
        sa.Column("first_name", sa.String(128), nullable=True),
        sa.Column("last_name", sa.String(128), nullable=True),
        sa.Column("notes", sa.String(1024), nullable=True),
        sa.UniqueConstraint("phone_hash", name="uq_person_phone_hash"),
    )
    # relationship
    op.create_table(
        "relationship",
        *create_base_columns(),
        sa.Column("business_id", sa.UUID(as_uuid=True), sa.ForeignKey("business.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_id", sa.UUID(as_uuid=True), sa.ForeignKey("person.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_on", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
    )
    # paymentrecord
    op.create_table(
        "paymentrecord",
        *create_base_columns(),
        sa.Column("business_id", sa.UUID(as_uuid=True), sa.ForeignKey("business.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_id", sa.UUID(as_uuid=True), sa.ForeignKey("person.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_id", sa.UUID(as_uuid=True), sa.ForeignKey("relationship.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Enum("pending", "paid", "late", "defaulted", name="paymentstatus"), nullable=False),
    )
    # trustscore
    op.create_table(
        "trustscore",
        *create_base_columns(),
        sa.Column("business_id", sa.UUID(as_uuid=True), sa.ForeignKey("business.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_id", sa.UUID(as_uuid=True), sa.ForeignKey("person.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("risk_band", sa.String(32), nullable=False),
        sa.Column("recommendation", sa.String(128), nullable=False),
        sa.Column("breakdown", sa.JSON(), nullable=False),
    )
    # reference
    op.create_table(
        "reference",
        *create_base_columns(),
        sa.Column("business_id", sa.UUID(as_uuid=True), sa.ForeignKey("business.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_id", sa.UUID(as_uuid=True), sa.ForeignKey("person.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("notes", sa.String(1024), nullable=True),
    )
    # auditlog
    op.create_table(
        "auditlog",
        *create_base_columns(),
        sa.Column("business_id", sa.UUID(as_uuid=True), sa.ForeignKey("business.id", ondelete="CASCADE"), nullable=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("businessuser.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("path", sa.String(255), nullable=False),
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("ip", sa.String(64), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
    )

def downgrade():
    op.drop_table("auditlog")
    op.drop_table("reference")
    op.drop_table("trustscore")
    op.drop_table("paymentrecord")
    op.drop_table("relationship")
    op.drop_table("person")
    op.drop_table("businessuser")
    op.drop_table("business")
    op.execute("DROP TYPE IF EXISTS paymentstatus")
