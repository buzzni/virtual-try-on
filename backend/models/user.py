from sqlalchemy import Column, String, Text, DateTime, TIMESTAMP, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    email = Column(Text, unique=True, nullable=True)
    profile_picture = Column(Text, nullable=True)
    google_social = Column(JSONB, nullable=True)
    kakao_social = Column(JSONB, nullable=True)
    language = Column(String(10), default="ko")
    phone_number = Column(String(32), nullable=True)
    organization_name = Column(Text, nullable=True)
    terms_agreed = Column(Boolean, nullable=False, default=False, server_default="false")
    privacy_agreed = Column(Boolean, nullable=False, default=False, server_default="false")
    marketing_agreed = Column(Boolean, nullable=False, default=False, server_default="false")
    user_type = Column(
        Enum("user", "manager", "admin", name="user_type_enum"),
        nullable=False,
        default="user",
        server_default="user",
    )
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
