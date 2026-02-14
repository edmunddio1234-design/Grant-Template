"""
SQLAlchemy ORM models for Grant Alignment Engine.

Defines all database entities with relationships, constraints, and indexes.
"""

from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, JSON,
    ForeignKey, Enum, Index, UniqueConstraint, CheckConstraint, ARRAY,
    UUID as SQLALCHEMY_UUID,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
import enum

from database import Base


class CategoryEnum(str, enum.Enum):
    """Enumeration for boilerplate categories."""
    ORGANIZATIONAL = "organizational"
    STAFFING = "staffing"
    PROGRAMS = "programs"
    EVALUATION = "evaluation"
    SUSTAINABILITY = "sustainability"
    COMPLIANCE = "compliance"


class EvidenceTypeEnum(str, enum.Enum):
    """Enumeration for evidence types."""
    QUANTITATIVE = "quantitative"
    QUALITATIVE = "qualitative"
    MIXED_METHODS = "mixed_methods"
    EVALUATION = "evaluation"
    RESEARCH = "research"


class RFPStatusEnum(str, enum.Enum):
    """Enumeration for RFP processing status."""
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    ANALYZED = "analyzed"
    ARCHIVED = "archived"


class AlignmentScoreEnum(str, enum.Enum):
    """Enumeration for alignment scoring."""
    STRONG = "strong"
    PARTIAL = "partial"
    WEAK = "weak"
    NONE = "none"


class RiskLevelEnum(str, enum.Enum):
    """Enumeration for risk levels."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class FundingTypeEnum(str, enum.Enum):
    """Enumeration for funding types."""
    FEDERAL = "federal"
    STATE = "state"
    FOUNDATION = "foundation"
    CORPORATE = "corporate"
    OTHER = "other"


class GrantPlanStatusEnum(str, enum.Enum):
    """Enumeration for grant plan status."""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    SUBMITTED = "submitted"


class TagTypeEnum(str, enum.Enum):
    """Enumeration for tag types."""
    PROGRAM = "program"
    FUNDING_TYPE = "funding_type"
    EVIDENCE = "evidence"
    PRIORITY_AREA = "priority_area"
    OUTCOME = "outcome"
    METRIC = "metric"


class UserRoleEnum(str, enum.Enum):
    """Enumeration for user roles."""
    ADMIN = "admin"
    GRANT_MANAGER = "grant_manager"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class ActionTypeEnum(str, enum.Enum):
    """Enumeration for audit log actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"


# ============================================================================
# BOILERPLATE CONTENT MODELS
# ============================================================================

class BoilerplateCategory(Base):
    """Boilerplate content categories."""
    __tablename__ = "boilerplate_categories"

    id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    sections: Mapped[list["BoilerplateSection"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_category_name", "name"),
        Index("idx_category_display_order", "display_order"),
    )


class BoilerplateSection(Base):
    """Boilerplate content sections with versioning."""
    __tablename__ = "boilerplate_sections"

    id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    category_id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        ForeignKey("boilerplate_categories.id", ondelete="CASCADE"),
        nullable=False
    )
    section_title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    evidence_type: Mapped[Optional[str]] = mapped_column(
        Enum(EvidenceTypeEnum),
        nullable=True
    )
    program_area: Mapped[Optional[str]] = mapped_column(String(255))
    compliance_relevance: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    category: Mapped["BoilerplateCategory"] = relationship(back_populates="sections")
    versions: Mapped[list["BoilerplateVersion"]] = relationship(
        back_populates="section",
        cascade="all, delete-orphan"
    )
    section_tags: Mapped[list["BoilerplateSectionTag"]] = relationship(
        back_populates="section",
        cascade="all, delete-orphan"
    )
    crosswalk_maps: Mapped[list["CrosswalkMap"]] = relationship(
        back_populates="boilerplate_section",
        cascade="all, delete-orphan"
    )
    grant_plan_sections: Mapped[list["GrantPlanSection"]] = relationship(
        back_populates="boilerplate_section"
    )

    __table_args__ = (
        Index("idx_section_category_id", "category_id"),
        Index("idx_section_is_active", "is_active"),
        Index("idx_section_program_area", "program_area"),
        Index("idx_section_title", "section_title"),
    )


class BoilerplateVersion(Base):
    """Version history for boilerplate sections."""
    __tablename__ = "boilerplate_versions"

    id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    section_id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        ForeignKey("boilerplate_sections.id", ondelete="CASCADE"),
        nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    change_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    section: Mapped["BoilerplateSection"] = relationship(back_populates="versions")

    __table_args__ = (
        Index("idx_version_section_id", "section_id"),
        Index("idx_version_number", "version_number"),
        UniqueConstraint("section_id", "version_number", name="uq_section_version"),
    )


# ============================================================================
# RFP MODELS
# ============================================================================

class RFP(Base):
    """Request for Proposal documents."""
    __tablename__ = "rfps"

    id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    funder_name: Mapped[str] = mapped_column(String(255), nullable=False)
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf, docx, txt, etc.
    status: Mapped[RFPStatusEnum] = mapped_column(
        Enum(RFPStatusEnum),
        default=RFPStatusEnum.UPLOADED
    )
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    funding_amount: Mapped[Optional[float]] = mapped_column(Float)
    funding_type: Mapped[Optional[str]] = mapped_column(
        Enum(FundingTypeEnum),
        nullable=True
    )
    eligibility_notes: Mapped[Optional[str]] = mapped_column(Text)
    raw_text: Mapped[Optional[str]] = mapped_column(Text)  # Full extracted text
    parsed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    requirements: Mapped[list["RFPRequirement"]] = relationship(
        back_populates="rfp",
        cascade="all, delete-orphan"
    )
    grant_plans: Mapped[list["GrantPlan"]] = relationship(
        back_populates="rfp",
        cascade="all, delete-orphan"
    )
    gap_analyses: Mapped[list["GapAnalysis"]] = relationship(
        back_populates="rfp",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_rfp_funder_name", "funder_name"),
        Index("idx_rfp_status", "status"),
        Index("idx_rfp_deadline", "deadline"),
        Index("idx_rfp_created_at", "created_at"),
    )


class RFPRequirement(Base):
    """Individual requirements extracted from RFPs."""
    __tablename__ = "rfp_requirements"

    id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    rfp_id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        ForeignKey("rfps.id", ondelete="CASCADE"),
        nullable=False
    )
    section_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    word_limit: Mapped[Optional[int]] = mapped_column(Integer)
    scoring_weight: Mapped[Optional[float]] = mapped_column(Float)
    formatting_notes: Mapped[Optional[str]] = mapped_column(Text)
    eligibility_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    required_attachments: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    section_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    rfp: Mapped["RFP"] = relationship(back_populates="requirements")
    crosswalk_maps: Mapped[list["CrosswalkMap"]] = relationship(
        back_populates="rfp_requirement",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_requirement_rfp_id", "rfp_id"),
        Index("idx_requirement_section_name", "section_name"),
    )


# ============================================================================
# CROSSWALK & ALIGNMENT MODELS
# ============================================================================

class CrosswalkMap(Base):
    """Maps RFP requirements to boilerplate sections."""
    __tablename__ = "crosswalk_maps"

    id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    rfp_requirement_id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        ForeignKey("rfp_requirements.id", ondelete="CASCADE"),
        nullable=False
    )
    boilerplate_section_id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        ForeignKey("boilerplate_sections.id", ondelete="CASCADE"),
        nullable=False
    )
    alignment_score: Mapped[AlignmentScoreEnum] = mapped_column(
        Enum(AlignmentScoreEnum),
        default=AlignmentScoreEnum.NONE
    )
    gap_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_level: Mapped[RiskLevelEnum] = mapped_column(
        Enum(RiskLevelEnum),
        default=RiskLevelEnum.GREEN
    )
    customization_needed: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_matched: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewer_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    rfp_requirement: Mapped["RFPRequirement"] = relationship(back_populates="crosswalk_maps")
    boilerplate_section: Mapped["BoilerplateSection"] = relationship(back_populates="crosswalk_maps")

    __table_args__ = (
        Index("idx_crosswalk_rfp_req_id", "rfp_requirement_id"),
        Index("idx_crosswalk_boilerplate_id", "boilerplate_section_id"),
        Index("idx_crosswalk_alignment_score", "alignment_score"),
        Index("idx_crosswalk_risk_level", "risk_level"),
        UniqueConstraint(
            "rfp_requirement_id",
            "boilerplate_section_id",
            name="uq_requirement_boilerplate"
        ),
    )


# ============================================================================
# GRANT PLAN MODELS
# ============================================================================

class GrantPlan(Base):
    """Grant application plans created for specific RFPs."""
    __tablename__ = "grant_plans"

    id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    rfp_id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        ForeignKey("rfps.id", ondelete="CASCADE"),
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[GrantPlanStatusEnum] = mapped_column(
        Enum(GrantPlanStatusEnum),
        default=GrantPlanStatusEnum.DRAFT
    )
    plan_data: Mapped[dict] = mapped_column(JSON, default={})  # Flexible metadata
    compliance_score: Mapped[Optional[float]] = mapped_column(
        Float,
        CheckConstraint("compliance_score >= 0 AND compliance_score <= 100")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    rfp: Mapped["RFP"] = relationship(back_populates="grant_plans")
    sections: Mapped[list["GrantPlanSection"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_plan_rfp_id", "rfp_id"),
        Index("idx_plan_status", "status"),
        Index("idx_plan_created_at", "created_at"),
    )


class GrantPlanSection(Base):
    """Individual sections within grant plans."""
    __tablename__ = "grant_plan_sections"

    id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    plan_id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        ForeignKey("grant_plans.id", ondelete="CASCADE"),
        nullable=False
    )
    boilerplate_section_id: Mapped[Optional[str]] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        ForeignKey("boilerplate_sections.id")
    )
    section_title: Mapped[str] = mapped_column(String(255), nullable=False)
    section_order: Mapped[int] = mapped_column(Integer, default=0)
    suggested_content: Mapped[Optional[str]] = mapped_column(Text)
    word_limit: Mapped[Optional[int]] = mapped_column(Integer)
    word_count_target: Mapped[Optional[int]] = mapped_column(Integer)
    customization_notes: Mapped[Optional[str]] = mapped_column(Text)
    compliance_status: Mapped[Optional[str]] = mapped_column(String(50))
    risk_level: Mapped[Optional[RiskLevelEnum]] = mapped_column(Enum(RiskLevelEnum))

    # Relationships
    plan: Mapped["GrantPlan"] = relationship(back_populates="sections")
    boilerplate_section: Mapped[Optional["BoilerplateSection"]] = relationship(
        back_populates="grant_plan_sections"
    )

    __table_args__ = (
        Index("idx_plan_section_plan_id", "plan_id"),
        Index("idx_plan_section_order", "section_order"),
    )


# ============================================================================
# GAP ANALYSIS MODELS
# ============================================================================

class GapAnalysis(Base):
    """Gap analysis results for RFPs."""
    __tablename__ = "gap_analyses"

    id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    rfp_id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        ForeignKey("rfps.id", ondelete="CASCADE"),
        nullable=False
    )
    analysis_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    overall_risk_level: Mapped[RiskLevelEnum] = mapped_column(
        Enum(RiskLevelEnum),
        default=RiskLevelEnum.GREEN
    )
    gap_data: Mapped[dict] = mapped_column(JSON, default={})
    recommendations: Mapped[dict] = mapped_column(JSON, default={})
    missing_metrics: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    weak_alignments: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    outdated_data: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    missing_partnerships: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    match_gaps: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    evaluation_weaknesses: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])

    # Relationships
    rfp: Mapped["RFP"] = relationship(back_populates="gap_analyses")

    __table_args__ = (
        Index("idx_gap_rfp_id", "rfp_id"),
        Index("idx_gap_analysis_date", "analysis_date"),
        Index("idx_gap_overall_risk_level", "overall_risk_level"),
    )


# ============================================================================
# TAG MODELS
# ============================================================================

class Tag(Base):
    """Tags for categorizing content."""
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    tag_type: Mapped[TagTypeEnum] = mapped_column(
        Enum(TagTypeEnum),
        nullable=False
    )

    # Relationships
    boilerplate_section_tags: Mapped[list["BoilerplateSectionTag"]] = relationship(
        back_populates="tag",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_tag_name", "name"),
        Index("idx_tag_type", "tag_type"),
    )


class BoilerplateSectionTag(Base):
    """Junction table for boilerplate sections and tags."""
    __tablename__ = "boilerplate_section_tags"

    id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    section_id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        ForeignKey("boilerplate_sections.id", ondelete="CASCADE"),
        nullable=False
    )
    tag_id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationships
    section: Mapped["BoilerplateSection"] = relationship(back_populates="section_tags")
    tag: Mapped["Tag"] = relationship(back_populates="boilerplate_section_tags")

    __table_args__ = (
        Index("idx_section_tag_section_id", "section_id"),
        Index("idx_section_tag_tag_id", "tag_id"),
        UniqueConstraint("section_id", "tag_id", name="uq_section_tag"),
    )


# ============================================================================
# USER & AUDIT MODELS
# ============================================================================

class User(Base):
    """System users."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRoleEnum] = mapped_column(
        Enum(UserRoleEnum),
        default=UserRoleEnum.VIEWER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_role", "role"),
        Index("idx_user_is_active", "is_active"),
    )


class AuditLog(Base):
    """Audit trail for system actions."""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    action: Mapped[ActionTypeEnum] = mapped_column(
        Enum(ActionTypeEnum),
        nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    old_value: Mapped[Optional[dict]] = mapped_column(JSON)
    new_value: Mapped[Optional[dict]] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_entity_type", "entity_type"),
        Index("idx_audit_entity_id", "entity_id"),
        Index("idx_audit_timestamp", "timestamp"),
    )


# ============================================================================
# NONPROFIT INTELLIGENCE MODELS (Funding Research)
# ============================================================================

class NonprofitOrg(Base):
    """Nonprofit organizations from ProPublica API."""
    __tablename__ = "nonprofit_orgs"

    ein: Mapped[str] = mapped_column(String(20), primary_key=True)
    name_legal: Mapped[str] = mapped_column(String(500), nullable=False)
    name_normalized: Mapped[str] = mapped_column(String(500), nullable=False)
    ntee_code: Mapped[Optional[str]] = mapped_column(String(20))
    subsection_code: Mapped[Optional[str]] = mapped_column(String(10))
    ruling_year: Mapped[Optional[int]] = mapped_column(Integer)
    address_line1: Mapped[Optional[str]] = mapped_column(String(500))
    city: Mapped[Optional[str]] = mapped_column(String(255))
    state: Mapped[Optional[str]] = mapped_column(String(10))
    zip: Mapped[Optional[str]] = mapped_column(String(20))
    mission: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(String(500))
    revenue_latest: Mapped[Optional[float]] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    filings: Mapped[list["NonprofitFiling990"]] = relationship(
        back_populates="org", cascade="all, delete-orphan"
    )
    personnel: Mapped[list["NonprofitPersonnel"]] = relationship(
        back_populates="org", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_np_org_name_normalized", "name_normalized"),
        Index("idx_np_org_state_city", "state", "city"),
        Index("idx_np_org_ntee", "ntee_code"),
        Index("idx_np_org_revenue", "revenue_latest"),
    )


class NonprofitFiling990(Base):
    """990 tax filings from ProPublica."""
    __tablename__ = "nonprofit_filings_990"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ein: Mapped[str] = mapped_column(
        String(20), ForeignKey("nonprofit_orgs.ein", ondelete="CASCADE"), nullable=False
    )
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)
    form_type: Mapped[str] = mapped_column(String(20), nullable=False)
    total_revenue: Mapped[Optional[float]] = mapped_column(Float)
    total_expenses: Mapped[Optional[float]] = mapped_column(Float)
    total_assets: Mapped[Optional[float]] = mapped_column(Float)
    total_liabilities: Mapped[Optional[float]] = mapped_column(Float)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500))
    xml_url: Mapped[Optional[str]] = mapped_column(String(500))
    filed_date: Mapped[Optional[str]] = mapped_column(String(20))
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="ProPublica")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    org: Mapped["NonprofitOrg"] = relationship(back_populates="filings")

    __table_args__ = (
        UniqueConstraint("ein", "tax_year", "form_type", name="uq_np_filing"),
        Index("idx_np_filing_ein_year", "ein", "tax_year"),
    )


class NonprofitPersonnel(Base):
    """Officers and key personnel from 990 filings."""
    __tablename__ = "nonprofit_personnel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ein: Mapped[str] = mapped_column(
        String(20), ForeignKey("nonprofit_orgs.ein", ondelete="CASCADE"), nullable=False
    )
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    compensation: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    org: Mapped["NonprofitOrg"] = relationship(back_populates="personnel")

    __table_args__ = (
        Index("idx_np_personnel_ein_year", "ein", "tax_year"),
    )


class NonprofitAward(Base):
    """Federal awards from USAspending API."""
    __tablename__ = "nonprofit_awards"

    award_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    recipient_ein: Mapped[Optional[str]] = mapped_column(String(20))
    recipient_name: Mapped[Optional[str]] = mapped_column(String(500))
    amount: Mapped[Optional[float]] = mapped_column(Float)
    action_date: Mapped[Optional[str]] = mapped_column(String(20))
    awarding_agency: Mapped[Optional[str]] = mapped_column(String(500))
    cfda_number: Mapped[Optional[str]] = mapped_column(String(50))
    award_type: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    recipient_city: Mapped[Optional[str]] = mapped_column(String(255))
    recipient_state: Mapped[Optional[str]] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_np_award_ein", "recipient_ein"),
        Index("idx_np_award_agency", "awarding_agency"),
        Index("idx_np_award_date", "action_date"),
    )


class NonprofitCache(Base):
    """Cache for upstream API responses with TTL."""
    __tablename__ = "nonprofit_cache"

    cache_key: Mapped[str] = mapped_column(String(500), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    ttl_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    cached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
