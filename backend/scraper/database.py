import os
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base


db_password = os.getenv("DB_PASSWORD")
db_user = os.getenv("DB_USER")
engine = sa.create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@localhost/npo_db")
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Role(Base):
    __tablename__ = "role"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()")
    )

    name: Mapped[str | None] = mapped_column(sa.String(50), nullable=False)

    description: Mapped[str | None] = mapped_column(sa.Text)

class User(Base):
    __tablename__ = "user"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()")
    )

    role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("role.role_id"),
        nullable=True
    )

    name: Mapped[str | None] = mapped_column(sa.String(100), nullable=False)

    email: Mapped[str | None] = mapped_column(sa.String(120), nullable=False, unique=True)

    password_hash: Mapped[str | None] = mapped_column(sa.Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP,
        server_default=sa.func.now()
    )

class DataSource(Base):
    __tablename__ = "data_source"

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()")
    )

    name: Mapped[str | None] = mapped_column(sa.String(100))

    url: Mapped[str | None] = mapped_column(sa.Text)

    last_scraped: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP,
        server_default=sa.func.now()
    )

class Organization(Base):
    __tablename__ = "organization"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()")
    )

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("data_source.source_id"),
        nullable=True
    )

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("organization.organization_id"),
        nullable=True
    )

    name: Mapped[str | None] = mapped_column(sa.String(200), nullable=False)

    ico: Mapped[str | None] = mapped_column(sa.String(20), nullable=False, unique=True)

    legal_form: Mapped[str | None] = mapped_column(sa.String(100))

    web_url: Mapped[str | None] = mapped_column(sa.Text)

    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP)

    hq_address: Mapped[str | None] = mapped_column(sa.Text)

    size_category: Mapped[str | None] = mapped_column(sa.String(50))

    size_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("size_category.cat_id"),
        nullable=True
    )

    emails: Mapped[list[str] | None] = mapped_column(ARRAY(sa.String(120)))

    tel_numbers: Mapped[list[str] | None] = mapped_column(ARRAY(sa.String(30)))

    description: Mapped[str | None] = mapped_column(sa.Text)

class SizeCategory(Base):
    __tablename__ = "size_category"

    cat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()")
    )

    label: Mapped[str] = mapped_column(sa.String(50))

    min_emp: Mapped[int] = mapped_column(sa.Integer)

    max_emp: Mapped[int | None] = mapped_column(sa.Integer)

class Branch(Base):
    __tablename__ = "branch"

    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()")
    )

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("organization.organization_id"),
        nullable=True
    )

    city: Mapped[str | None] = mapped_column(sa.String(100))

    street: Mapped[str | None] = mapped_column(sa.String(150))

    email: Mapped[str | None] = mapped_column(sa.String(120))

    tel_num: Mapped[str | None] = mapped_column(sa.String(30))

    lat: Mapped[float | None] = mapped_column(sa.Float)

    lon: Mapped[float | None] = mapped_column(sa.Float)

    __table_args__ = (
        sa.UniqueConstraint("organization_id", "lat", "lon", name="uq_branch_org_lat_lon"),
    )

class Category(Base):
    __tablename__ = "category"

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()")
    )

    name: Mapped[str] = mapped_column(sa.String(100), unique=True, nullable=False)

class OrganizationCategory(Base):
    __tablename__ = "organization_category"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("organization.organization_id"),
        primary_key=True
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("category.category_id"),
        primary_key=True
    )

class NpoManager(Base):
    __tablename__ = "npo_manager"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("user.user_id"),
        primary_key=True
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("organization.organization_id"),
        primary_key=True
    )
