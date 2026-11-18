from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    domain: Mapped[str | None] = mapped_column(
        String(255),
        index=True,
        unique=True,
    )
    website: Mapped[str | None] = mapped_column(String(500))
    country: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    nz_relevance: Mapped[int] = mapped_column(Integer, default=0)
    au_relevance: Mapped[int] = mapped_column(Integer, default=0)
    voice_relevance: Mapped[int] = mapped_column(Integer, default=0)
    company_score: Mapped[int] = mapped_column(Integer, default=0)
    # JSON-encoded list of {signal, points, matched} explaining company_score.
    score_rationale: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(100))
    source_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    contacts: Mapped[list["Contact"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    job_title: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(80))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    country: Mapped[str | None] = mapped_column(String(100))
    contact_score: Mapped[int] = mapped_column(Integer, default=0)
    email_status: Mapped[str | None] = mapped_column(String(50))
    email_source: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    company: Mapped["Company"] = relationship(back_populates="contacts")
    outreach: Mapped[list["Outreach"]] = relationship(back_populates="contact", cascade="all, delete-orphan")
    responses: Mapped[list["Response"]] = relationship(back_populates="contact", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    __table_args__ = (
        UniqueConstraint("company_id", "url", name="uq_evidence_company_url"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    url: Mapped[str | None] = mapped_column(String(1000))
    page_title: Mapped[str | None] = mapped_column(String(500))
    evidence_type: Mapped[str | None] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(Text)
    relevance_score: Mapped[int] = mapped_column(Integer, default=0)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    company: Mapped["Company"] = relationship(back_populates="evidence")


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    channel: Mapped[str] = mapped_column(String(50), default="email")
    daily_limit: Mapped[int] = mapped_column(Integer, default=20)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )


class Outreach(Base):
    __tablename__ = "outreach"

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"))
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(50), default="email")
    sequence_no: Mapped[int] = mapped_column(Integer, default=1)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)
    subject: Mapped[str | None] = mapped_column(String(500))
    body: Mapped[str | None] = mapped_column(Text)
    delivery_status: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    contact: Mapped["Contact"] = relationship(back_populates="outreach")


class Response(Base):
    __tablename__ = "responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"))
    received_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    channel: Mapped[str] = mapped_column(String(50), default="email")
    body: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(80))
    confidence: Mapped[float | None] = mapped_column(Float)
    next_action: Mapped[str | None] = mapped_column(String(100))

    contact: Mapped["Contact"] = relationship(back_populates="responses")


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"))
    stage: Mapped[str] = mapped_column(String(80), default="new")
    estimated_minutes: Mapped[float | None] = mapped_column(Float)
    current_rate: Mapped[float | None] = mapped_column(Float)
    proposed_rate: Mapped[float | None] = mapped_column(Float)
    estimated_value: Mapped[float | None] = mapped_column(Float)
    owner: Mapped[str | None] = mapped_column(String(255))
    next_action: Mapped[str | None] = mapped_column(String(500))


class Suppression(Base):
    __tablename__ = "suppression"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(80), index=True)
    domain: Mapped[str | None] = mapped_column(String(255), index=True)
    reason: Mapped[str] = mapped_column(String(255))
    source: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

class ContactPermission(Base):
    __tablename__ = "contact_permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"))
    country: Mapped[str | None] = mapped_column(String(100))
    source_type: Mapped[str | None] = mapped_column(String(100))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    consent_status: Mapped[str] = mapped_column(String(50), default="unknown")
    consent_date: Mapped[datetime | None] = mapped_column(DateTime)
    consent_evidence: Mapped[str | None] = mapped_column(Text)
    lawful_basis: Mapped[str | None] = mapped_column(String(255))
    last_checked: Mapped[datetime | None] = mapped_column(DateTime)
    notes: Mapped[str | None] = mapped_column(Text)
