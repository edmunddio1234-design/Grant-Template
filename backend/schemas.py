"""
Pydantic v2 schemas for API request/response validation.

Defines all data models for API endpoints with proper validation and documentation.
"""

from datetime import datetime
from uuid import UUID
from typing import Optional, Generic, TypeVar, List, Any, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum

# Import enums from models for reuse
from models import (
    AlignmentScoreEnum,
    RiskLevelEnum,
    RFPStatusEnum,
    FundingTypeEnum,
    GrantPlanStatusEnum,
    UserRoleEnum,
    EvidenceTypeEnum,
    TagTypeEnum,
)


# ============================================================================
# GENERIC TYPES & UTILITIES
# ============================================================================

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum items to return")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    total: int = Field(description="Total number of items")
    skip: int = Field(description="Number of items skipped")
    limit: int = Field(description="Items per page")
    items: List[T] = Field(description="Page items")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 100,
                "skip": 0,
                "limit": 20,
                "items": []
            }
        }
    )


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )


# ============================================================================
# BOILERPLATE SCHEMAS
# ============================================================================

class BoilerplateCategoryBase(BaseSchema):
    """Base boilerplate category schema."""
    name: str = Field(min_length=1, max_length=255, description="Category name")
    description: str = Field(description="Category description")
    display_order: int = Field(default=0, ge=0, description="Display order")


class BoilerplateCategoryCreate(BoilerplateCategoryBase):
    """Create boilerplate category schema."""
    pass


class BoilerplateCategoryRead(BoilerplateCategoryBase):
    """Read boilerplate category schema."""
    id: UUID = Field(description="Category ID")
    created_at: datetime = Field(description="Creation timestamp")


class BoilerplateSectionBase(BaseSchema):
    """Base boilerplate section schema."""
    section_title: str = Field(min_length=1, max_length=255, description="Section title")
    content: str = Field(min_length=1, description="Section content")
    evidence_type: Optional[EvidenceTypeEnum] = Field(default=None, description="Evidence type")
    program_area: Optional[str] = Field(default=None, max_length=255, description="Program area")
    compliance_relevance: Optional[str] = Field(default=None, description="Compliance notes")
    is_active: bool = Field(default=True, description="Is section active?")
    tags: List[str] = Field(default=[], description="Associated tags")


class BoilerplateSectionCreate(BoilerplateSectionBase):
    """Create boilerplate section schema."""
    category_id: UUID = Field(description="Category ID")
    created_by: Optional[str] = Field(default=None, max_length=255, description="Creator email")


class BoilerplateSectionUpdate(BaseSchema):
    """Update boilerplate section schema."""
    section_title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content: Optional[str] = Field(default=None, min_length=1)
    evidence_type: Optional[EvidenceTypeEnum] = None
    program_area: Optional[str] = None
    compliance_relevance: Optional[str] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


class BoilerplateSectionRead(BoilerplateSectionBase):
    """Read boilerplate section schema."""
    id: UUID = Field(description="Section ID")
    category_id: UUID = Field(description="Category ID")
    version: int = Field(description="Current version")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    created_by: Optional[str] = None
    last_updated: datetime = Field(description="Last updated timestamp")


class BoilerplateVersionRead(BaseSchema):
    """Read boilerplate version schema."""
    id: UUID = Field(description="Version ID")
    section_id: UUID = Field(description="Section ID")
    version_number: int = Field(description="Version number")
    content: str = Field(description="Version content")
    changed_by: str = Field(description="User who made changes")
    changed_at: datetime = Field(description="Change timestamp")
    change_notes: Optional[str] = None


# ============================================================================
# RFP SCHEMAS
# ============================================================================

class RFPBase(BaseSchema):
    """Base RFP schema."""
    title: str = Field(min_length=1, max_length=500, description="RFP title")
    funder_name: str = Field(min_length=1, max_length=255, description="Funder name")
    file_type: str = Field(max_length=10, description="File type (pdf, docx, etc)")
    deadline: Optional[datetime] = Field(default=None, description="Application deadline")
    funding_amount: Optional[float] = Field(default=None, ge=0, description="Funding amount")
    funding_type: Optional[FundingTypeEnum] = None
    eligibility_notes: Optional[str] = None


class RFPCreate(RFPBase):
    """Create RFP schema."""
    file_path: str = Field(min_length=1, description="File storage path")


class RFPUpdate(BaseSchema):
    """Update RFP schema."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    funder_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    deadline: Optional[datetime] = None
    funding_amount: Optional[float] = None
    funding_type: Optional[FundingTypeEnum] = None
    eligibility_notes: Optional[str] = None
    status: Optional[RFPStatusEnum] = None


class RFPRead(RFPBase):
    """Read RFP schema."""
    id: UUID = Field(description="RFP ID")
    file_path: str = Field(description="File storage path")
    status: RFPStatusEnum = Field(description="Processing status")
    upload_date: datetime = Field(description="Upload timestamp")
    parsed_at: Optional[datetime] = None
    created_at: datetime = Field(description="Creation timestamp")
    raw_text: Optional[str] = Field(default=None, description="Extracted text (truncated)")


class RFPListRead(BaseSchema):
    """Simplified RFP for list endpoints."""
    id: UUID
    title: str
    funder_name: str
    status: RFPStatusEnum
    deadline: Optional[datetime] = None
    funding_amount: Optional[float] = None
    upload_date: datetime


class RFPRequirementRead(BaseSchema):
    """Read RFP requirement schema."""
    id: UUID = Field(description="Requirement ID")
    rfp_id: UUID = Field(description="RFP ID")
    section_name: str = Field(description="Section name")
    description: str = Field(description="Requirement description")
    word_limit: Optional[int] = None
    scoring_weight: Optional[float] = None
    formatting_notes: Optional[str] = None
    eligibility_flag: bool = Field(description="Is eligibility requirement?")
    required_attachments: List[str] = Field(default=[], description="Required attachments")
    section_order: int = Field(default=0)


# ============================================================================
# CROSSWALK & ALIGNMENT SCHEMAS
# ============================================================================

class CrosswalkMapBase(BaseSchema):
    """Base crosswalk map schema."""
    alignment_score: AlignmentScoreEnum = Field(description="Alignment score")
    gap_flag: bool = Field(default=False, description="Gap identified?")
    risk_level: RiskLevelEnum = Field(description="Risk level")
    customization_needed: bool = Field(default=False)
    auto_matched: bool = Field(default=False)
    reviewer_approved: bool = Field(default=False)
    notes: Optional[str] = None


class CrosswalkMapCreate(CrosswalkMapBase):
    """Create crosswalk map schema."""
    rfp_requirement_id: UUID = Field(description="RFP requirement ID")
    boilerplate_section_id: UUID = Field(description="Boilerplate section ID")


class CrosswalkMapUpdate(BaseSchema):
    """Update crosswalk map schema."""
    alignment_score: Optional[AlignmentScoreEnum] = None
    gap_flag: Optional[bool] = None
    risk_level: Optional[RiskLevelEnum] = None
    customization_needed: Optional[bool] = None
    auto_matched: Optional[bool] = None
    reviewer_approved: Optional[bool] = None
    notes: Optional[str] = None


class CrosswalkMapRead(CrosswalkMapBase):
    """Read crosswalk map schema."""
    id: UUID = Field(description="Crosswalk ID")
    rfp_requirement_id: UUID = Field(description="RFP requirement ID")
    boilerplate_section_id: UUID = Field(description="Boilerplate section ID")


class CrosswalkResult(BaseSchema):
    """Side-by-side crosswalk result for display."""
    rfp_requirement: RFPRequirementRead = Field(description="RFP requirement details")
    boilerplate_section: BoilerplateSectionRead = Field(description="Boilerplate section details")
    alignment_score: AlignmentScoreEnum = Field(description="Alignment score")
    risk_level: RiskLevelEnum = Field(description="Risk level")
    gap_flag: bool = Field(description="Gap identified?")
    customization_needed: bool = Field(description="Customization needed?")
    notes: Optional[str] = None


class AlignmentMatrixRow(BaseSchema):
    """Row in alignment matrix for dashboard."""
    requirement_id: UUID = Field(description="RFP requirement ID")
    requirement_title: str = Field(description="Requirement title")
    boilerplate_id: UUID = Field(description="Boilerplate section ID")
    boilerplate_title: str = Field(description="Boilerplate title")
    alignment_score: AlignmentScoreEnum = Field(description="Alignment score")
    risk_level: RiskLevelEnum = Field(description="Risk level")
    word_limit: Optional[int] = None
    gap_flag: bool = Field(description="Gap identified?")
    customization_needed: bool = Field(description="Customization needed?")


class ComplianceChecklistItem(BaseSchema):
    """Item in compliance checklist."""
    item_id: str = Field(description="Unique item identifier")
    category: str = Field(description="Checklist category")
    description: str = Field(description="Item description")
    is_complete: bool = Field(default=False, description="Is item complete?")
    risk_level: RiskLevelEnum = Field(description="Risk level")
    notes: Optional[str] = None
    remediation_steps: Optional[List[str]] = None


# ============================================================================
# GRANT PLAN SCHEMAS
# ============================================================================

class GrantPlanSectionBase(BaseSchema):
    """Base grant plan section schema."""
    section_title: str = Field(min_length=1, max_length=255, description="Section title")
    section_order: int = Field(default=0, ge=0, description="Display order")
    suggested_content: Optional[str] = None
    word_limit: Optional[int] = Field(default=None, ge=0)
    word_count_target: Optional[int] = Field(default=None, ge=0)
    customization_notes: Optional[str] = None
    compliance_status: Optional[str] = None
    risk_level: Optional[RiskLevelEnum] = None


class GrantPlanSectionRead(GrantPlanSectionBase):
    """Read grant plan section schema."""
    id: UUID = Field(description="Section ID")
    plan_id: UUID = Field(description="Plan ID")
    boilerplate_section_id: Optional[UUID] = None


class GrantPlanBase(BaseSchema):
    """Base grant plan schema."""
    title: str = Field(min_length=1, max_length=500, description="Plan title")
    status: GrantPlanStatusEnum = Field(default=GrantPlanStatusEnum.DRAFT)
    compliance_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Compliance score percentage"
    )
    plan_data: Dict[str, Any] = Field(default={}, description="Flexible plan metadata")


class GrantPlanCreate(GrantPlanBase):
    """Create grant plan schema."""
    rfp_id: UUID = Field(description="RFP ID")
    created_by: Optional[str] = Field(default=None, max_length=255)


class GrantPlanUpdate(BaseSchema):
    """Update grant plan schema."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    status: Optional[GrantPlanStatusEnum] = None
    compliance_score: Optional[float] = None
    plan_data: Optional[Dict[str, Any]] = None


class GrantPlanRead(GrantPlanBase):
    """Read grant plan schema."""
    id: UUID = Field(description="Plan ID")
    rfp_id: UUID = Field(description="RFP ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    created_by: Optional[str] = None
    sections: List[GrantPlanSectionRead] = Field(default=[], description="Plan sections")


# ============================================================================
# GAP ANALYSIS SCHEMAS
# ============================================================================

class GapAnalysisRead(BaseSchema):
    """Read gap analysis schema."""
    id: UUID = Field(description="Analysis ID")
    rfp_id: UUID = Field(description="RFP ID")
    analysis_date: datetime = Field(description="Analysis timestamp")
    overall_risk_level: RiskLevelEnum = Field(description="Overall risk level")
    missing_metrics: List[str] = Field(default=[], description="Missing metrics")
    weak_alignments: List[str] = Field(default=[], description="Weak alignments")
    outdated_data: List[str] = Field(default=[], description="Outdated data areas")
    missing_partnerships: List[str] = Field(default=[], description="Missing partnerships")
    match_gaps: List[str] = Field(default=[], description="Requirement match gaps")
    evaluation_weaknesses: List[str] = Field(default=[], description="Evaluation weaknesses")
    gap_data: Dict[str, Any] = Field(default={}, description="Detailed gap analysis data")
    recommendations: Dict[str, Any] = Field(default={}, description="Recommendations")


# ============================================================================
# TAG SCHEMAS
# ============================================================================

class TagBase(BaseSchema):
    """Base tag schema."""
    name: str = Field(min_length=1, max_length=100, description="Tag name")
    tag_type: TagTypeEnum = Field(description="Tag type")


class TagCreate(TagBase):
    """Create tag schema."""
    pass


class TagRead(TagBase):
    """Read tag schema."""
    id: UUID = Field(description="Tag ID")


# ============================================================================
# USER & AUTHENTICATION SCHEMAS
# ============================================================================

class UserBase(BaseSchema):
    """Base user schema."""
    email: str = Field(description="User email")
    name: str = Field(min_length=1, max_length=255, description="User name")
    role: UserRoleEnum = Field(default=UserRoleEnum.VIEWER)


class UserCreate(UserBase):
    """Create user schema."""
    password: str = Field(min_length=8, description="User password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email format")
        return v.lower()


class UserUpdate(BaseSchema):
    """Update user schema."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    role: Optional[UserRoleEnum] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    """Read user schema."""
    id: UUID = Field(description="User ID")
    is_active: bool = Field(description="Is user active?")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class TokenResponse(BaseModel):
    """JWT token response schema."""
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(default="bearer")
    expires_in: int = Field(description="Token expiration in seconds")


# ============================================================================
# DASHBOARD & SUMMARY SCHEMAS
# ============================================================================

class RiskDashboardSummary(BaseSchema):
    """Dashboard risk summary."""
    total_rfps: int = Field(description="Total RFPs")
    high_risk_count: int = Field(description="RFPs with high risk")
    medium_risk_count: int = Field(description="RFPs with medium risk")
    low_risk_count: int = Field(description="RFPs with low risk")
    average_compliance_score: float = Field(description="Average compliance score")
    gaps_requiring_attention: int = Field(description="Critical gaps count")
    plans_in_progress: int = Field(description="Grant plans in progress")
    upcoming_deadlines: List[Dict[str, Any]] = Field(
        default=[],
        description="Upcoming deadline summaries"
    )


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(description="Service status")
    timestamp: datetime = Field(description="Check timestamp")
    database: str = Field(description="Database status")
    redis: str = Field(description="Redis status")
    version: str = Field(description="API version")
