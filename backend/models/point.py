from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from db.session import Base


class Point(Base):
    __tablename__ = "points"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    credit = Column(Integer, default=0, nullable=False)
    look_book_ticket = Column(Integer, default=0, nullable=False)
    video_ticket = Column(Integer, default=0, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class PointUsage(Base):
    __tablename__ = "point_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    job_id = Column(UUID(as_uuid=True), nullable=True)
    usage_type = Column(String(32), nullable=False)
    usage_method = Column(String(32), nullable=False)
    amount = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
