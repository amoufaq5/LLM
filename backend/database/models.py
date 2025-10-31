"""
Database models for Lumen Medical LLM
HIPAA-compliant with encryption and audit logging
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.database.base import Base


class UserRole(str, Enum):
    """User roles in the system"""

    PATIENT = "patient"
    DOCTOR = "doctor"
    PHARMACIST = "pharmacist"
    PHARMA_COMPANY = "pharma_company"
    STUDENT = "student"
    RESEARCHER = "researcher"
    ADMIN = "admin"


class MessageRole(str, Enum):
    """Message roles in conversation"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class User(Base):
    """User account model"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    patient_profile: Mapped[Optional["PatientProfile"]] = relationship(
        "PatientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class PatientProfile(Base):
    """
    Patient profile model
    Stores medical history and health information
    All PHI (Protected Health Information) should be encrypted at rest
    """

    __tablename__ = "patient_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Demographics (encrypted in production)
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    gender: Mapped[Optional[str]] = mapped_column(String(50))
    blood_type: Mapped[Optional[str]] = mapped_column(String(10))

    # Medical History (stored as JSON, encrypted in production)
    medical_conditions: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    current_medications: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    allergies: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    past_surgeries: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    family_history: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Lifestyle
    smoking_status: Mapped[Optional[str]] = mapped_column(String(50))
    alcohol_consumption: Mapped[Optional[str]] = mapped_column(String(50))
    exercise_frequency: Mapped[Optional[str]] = mapped_column(String(50))

    # Emergency Contact (encrypted)
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(255))
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(50))
    emergency_contact_relationship: Mapped[Optional[str]] = mapped_column(String(100))

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="patient_profile")

    def __repr__(self) -> str:
        return f"<PatientProfile(id={self.id}, user_id={self.user_id})>"


class Conversation(Base):
    """Conversation thread between user and AI"""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(
        String(100)
    )  # medical_qa, symptom_check, pharma_compliance, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id}, title={self.title})>"


class Message(Base):
    """Individual message in a conversation"""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    role: Mapped[MessageRole] = mapped_column(SQLEnum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # RAG metadata
    sources: Mapped[Optional[dict]] = mapped_column(JSON)  # Sources used for RAG
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)

    # Feedback
    user_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 stars
    user_feedback: Mapped[Optional[str]] = mapped_column(Text)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role={self.role})>"


class AuditLog(Base):
    """
    Audit log for HIPAA compliance
    Tracks all access to PHI and sensitive operations
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    # Action details
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255))
    details: Mapped[Optional[dict]] = mapped_column(JSON)

    # Request metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 max length
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))

    # Result
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action})>"
