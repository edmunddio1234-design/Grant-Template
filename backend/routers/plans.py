"""
Grant Plan Generation Routes - Module 4

Routes for generating, managing, and exporting grant plans for Project Family Build
and other grant initiatives.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from database import get_db
from dependencies import get_current_user
from models import (
    GrantPlan,
    GrantPlanSection,
    RFP,
    RFPRequirement,
    GrantPlanStatusEnum,
    RiskLevelEnum,
    ActionTypeEnum,
    AuditLog,
    User,
)
from schemas import (
    GrantPlanCreate,
    GrantPlanRead,
    GrantPlanUpdate,
    GrantPlanSectionRead,
    ComplianceChecklistItem,
    PaginatedResponse,
)

# Import services (adjust based on actual implementation)
# from services import PlanGeneratorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/plans", tags=["plans"])


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


async def log_audit(
    db: AsyncSession,
    action: ActionTypeEnum,
    entity_type: str,
    entity_id: str,
    old_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
) -> None:
    """Log action to audit trail."""
    audit_log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
    )
    db.add(audit_log)


# ============================================================================
# GENERATION ENDPOINTS
# ============================================================================


@router.post(
    "/generate/{rfp_id}",
    response_model=GrantPlanRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a grant plan for an RFP",
)
async def generate_plan(
    rfp_id: UUID,
    plan_title: Optional[str] = Query(None, description="Custom plan title"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GrantPlanRead:
    """
    Generate a complete grant plan for an RFP.

    This endpoint:
    1. Fetches crosswalk results and gap analysis for the RFP
    2. Runs the PlanGeneratorService
    3. Creates GrantPlan and GrantPlanSection records
    4. Returns the generated plan

    Args:
        rfp_id: The RFP UUID.
        plan_title: Optional custom plan title.
        db: Database session.

    Returns:
        GrantPlanRead: Generated plan with sections.

    Raises:
        HTTPException: If RFP not found or generation fails.
    """
    try:
        # Load RFP with its parsed requirements
        rfp_result = await db.execute(
            select(RFP).options(selectinload(RFP.requirements)).where(RFP.id == str(rfp_id))
        )
        rfp = rfp_result.scalar_one_or_none()
        if not rfp:
            logger.warning(f"RFP not found: {rfp_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFP not found",
            )

        # Create grant plan
        plan = GrantPlan(
            rfp_id=rfp_id,
            title=plan_title or f"Grant Plan for {rfp.title}",
            status=GrantPlanStatusEnum.DRAFT,
            compliance_score=0.0,
            created_by="system",
        )

        db.add(plan)
        await db.flush()

        # Build plan sections from real RFP requirements
        requirements = sorted(rfp.requirements, key=lambda r: r.section_order) if rfp.requirements else []

        if requirements:
            # Create a plan section for each parsed RFP requirement
            for idx, req in enumerate(requirements):
                section = GrantPlanSection(
                    plan_id=plan.id,
                    section_title=req.section_name,
                    section_order=idx,
                    word_limit=req.word_limit,
                    suggested_content=req.description or f"Address the '{req.section_name}' requirement per the RFP.",
                    customization_notes=(
                        f"Scoring weight: {req.scoring_weight}" if req.scoring_weight else None
                    ),
                    compliance_status="pending",
                )
                db.add(section)
            logger.info(f"Created {len(requirements)} plan sections from RFP requirements")
        else:
            # Fallback: generate sensible default sections if no requirements were parsed
            logger.warning(f"No parsed requirements for RFP {rfp_id} — using default sections")
            default_sections = [
                ("Executive Summary", "Provide a concise overview of the proposed project, including goals, target population, and expected outcomes."),
                ("Organization Background", "Describe the organization's mission, history, capacity, and relevant experience."),
                ("Project Description", "Detail the proposed project activities, methodology, and implementation plan."),
                ("Target Population", "Describe the population to be served, including demographics and needs assessment."),
                ("Goals and Objectives", "List SMART goals and measurable objectives aligned with funder priorities."),
                ("Evaluation Plan", "Outline data collection methods, outcome measurements, and reporting strategies."),
                ("Budget Narrative", "Justify all budget line items and demonstrate cost-effectiveness."),
                ("Sustainability Plan", "Describe how the project will be sustained beyond the grant period."),
            ]
            for idx, (title, content) in enumerate(default_sections):
                section = GrantPlanSection(
                    plan_id=plan.id,
                    section_title=title,
                    section_order=idx,
                    suggested_content=content,
                    compliance_status="pending",
                )
                db.add(section)

        await db.commit()
        await db.refresh(plan)

        # Load sections
        await db.refresh(plan, ["sections"])

        # Log audit
        await log_audit(
            db,
            ActionTypeEnum.CREATE,
            "GrantPlan",
            str(plan.id),
            new_value={"title": plan.title, "rfp_id": str(rfp_id)},
        )
        await db.commit()

        logger.info(f"Generated plan: {plan.id} for RFP {rfp_id}")

        return GrantPlanRead.model_validate(plan)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating plan: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate plan",
        )


# ============================================================================
# LIST & RETRIEVE ENDPOINTS
# ============================================================================


@router.get(
    "/",
    response_model=PaginatedResponse[GrantPlanRead],
    summary="List all grant plans",
    status_code=status.HTTP_200_OK,
)
async def list_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[GrantPlanStatusEnum] = Query(None, description="Filter by status"),
    rfp_id: Optional[UUID] = Query(None, description="Filter by RFP"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[GrantPlanRead]:
    """
    List all grant plans with optional filtering.

    Args:
        skip: Pagination offset.
        limit: Pagination limit.
        status_filter: Filter by plan status.
        rfp_id: Filter by RFP.
        db: Database session.

    Returns:
        PaginatedResponse: Paginated list of plans.
    """
    try:
        filters = []
        if status_filter:
            filters.append(GrantPlan.status == status_filter)
        if rfp_id:
            filters.append(GrantPlan.rfp_id == rfp_id)

        # Count total
        count_query = select(func.count()).select_from(GrantPlan)
        if filters:
            count_query = count_query.where(and_(*filters))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Fetch plans with eager-loaded sections (required for async SQLAlchemy)
        query = select(GrantPlan).options(selectinload(GrantPlan.sections)).order_by(GrantPlan.created_at.desc())
        if filters:
            query = query.where(and_(*filters))

        result = await db.execute(query.offset(skip).limit(limit))
        plans = result.scalars().all()

        logger.info(f"Retrieved {len(plans)} plans (skip={skip}, limit={limit})")

        return PaginatedResponse(
            total=total,
            skip=skip,
            limit=limit,
            items=[GrantPlanRead.model_validate(plan) for plan in plans],
        )
    except Exception as e:
        logger.error(f"Error listing plans: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plans",
        )


@router.get(
    "/{plan_id}",
    response_model=GrantPlanRead,
    summary="Get grant plan details with sections",
    status_code=status.HTTP_200_OK,
)
async def get_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GrantPlanRead:
    """
    Retrieve a single grant plan with all its sections.

    Args:
        plan_id: The plan UUID.
        db: Database session.

    Returns:
        GrantPlanRead: Plan details.

    Raises:
        HTTPException: If plan not found.
    """
    try:
        result = await db.execute(
            select(GrantPlan).options(selectinload(GrantPlan.sections)).where(GrantPlan.id == str(plan_id))
        )
        plan = result.scalar_one_or_none()
        if not plan:
            logger.warning(f"Plan not found: {plan_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        logger.info(f"Retrieved plan: {plan_id}")

        return GrantPlanRead.model_validate(plan)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plan",
        )


# ============================================================================
# SECTION MANAGEMENT ENDPOINTS
# ============================================================================


@router.get(
    "/{plan_id}/sections",
    response_model=List[GrantPlanSectionRead],
    summary="Get plan sections",
    status_code=status.HTTP_200_OK,
)
async def get_plan_sections(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[GrantPlanSectionRead]:
    """
    Retrieve all sections for a grant plan.

    Args:
        plan_id: The plan UUID.
        db: Database session.

    Returns:
        List[GrantPlanSectionRead]: Plan sections.

    Raises:
        HTTPException: If plan not found.
    """
    try:
        # Verify plan exists
        plan = await db.get(GrantPlan, str(plan_id))
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        # Get sections
        result = await db.execute(
            select(GrantPlanSection)
            .where(GrantPlanSection.plan_id == plan_id)
            .order_by(GrantPlanSection.section_order)
        )
        sections = result.scalars().all()

        logger.info(f"Retrieved {len(sections)} sections for plan {plan_id}")

        return [GrantPlanSectionRead.model_validate(sec) for sec in sections]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving plan sections: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sections",
        )


@router.put(
    "/{plan_id}/sections/{section_id}",
    response_model=GrantPlanSectionRead,
    status_code=status.HTTP_200_OK,
    summary="Edit a plan section",
)
async def update_plan_section(
    plan_id: UUID,
    section_id: UUID,
    update_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GrantPlanSectionRead:
    """
    Update a grant plan section.

    Args:
        plan_id: The plan UUID.
        section_id: The section UUID.
        update_data: Updated section data.
        db: Database session.

    Returns:
        GrantPlanSectionRead: Updated section.

    Raises:
        HTTPException: If plan or section not found.
    """
    try:
        # Verify plan exists
        plan = await db.get(GrantPlan, str(plan_id))
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        # Get section
        section = await db.get(GrantPlanSection, str(section_id))
        if not section or section.plan_id != plan_id:
            logger.warning(f"Section not found: {section_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found",
            )

        # Store old values
        old_value = {
            "section_title": section.section_title,
            "suggested_content": section.suggested_content[:100] if section.suggested_content else None,
        }

        # Update fields
        for key, value in update_data.items():
            if hasattr(section, key):
                setattr(section, key, value)

        db.add(section)
        await db.commit()
        await db.refresh(section)

        # Log audit
        await log_audit(
            db,
            ActionTypeEnum.UPDATE,
            "GrantPlanSection",
            str(section.id),
            old_value=old_value,
            new_value=update_data,
        )
        await db.commit()

        logger.info(f"Updated plan section: {section_id}")

        return GrantPlanSectionRead.from_orm(section)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating plan section: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update section",
        )


# ============================================================================
# STATUS & LIFECYCLE ENDPOINTS
# ============================================================================


@router.put(
    "/{plan_id}/status",
    response_model=GrantPlanRead,
    status_code=status.HTTP_200_OK,
    summary="Update plan status",
)
async def update_plan_status(
    plan_id: UUID,
    status: GrantPlanStatusEnum,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GrantPlanRead:
    """
    Update the status of a grant plan (draft/review/approved/submitted).

    Args:
        plan_id: The plan UUID.
        status: New status.
        db: Database session.

    Returns:
        GrantPlanRead: Updated plan.

    Raises:
        HTTPException: If plan not found.
    """
    try:
        plan = await db.get(GrantPlan, str(plan_id))
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        old_status = plan.status
        plan.status = status
        db.add(plan)
        await db.commit()
        await db.refresh(plan)

        # Log audit
        await log_audit(
            db,
            ActionTypeEnum.UPDATE,
            "GrantPlan",
            str(plan.id),
            old_value={"status": old_status.value},
            new_value={"status": status.value},
        )
        await db.commit()

        logger.info(f"Updated plan {plan_id} status: {old_status} -> {status}")

        return GrantPlanRead.model_validate(plan)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating plan status: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update plan status",
        )


# ============================================================================
# COMPLIANCE ENDPOINTS
# ============================================================================


@router.get(
    "/{plan_id}/compliance",
    response_model=List[ComplianceChecklistItem],
    summary="Get compliance checklist",
    status_code=status.HTTP_200_OK,
)
async def get_compliance_checklist(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ComplianceChecklistItem]:
    """
    Get compliance checklist for a grant plan.

    Args:
        plan_id: The plan UUID.
        db: Database session.

    Returns:
        List[ComplianceChecklistItem]: Compliance items.

    Raises:
        HTTPException: If plan not found.
    """
    try:
        # Verify plan exists
        plan = await db.get(GrantPlan, str(plan_id))
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        # Build compliance checklist
        checklist = [
            ComplianceChecklistItem(
                item_id="01_project_description",
                category="Project Description",
                description="Project clearly describes target population and services",
                is_complete=False,
                risk_level=RiskLevelEnum.YELLOW,
                remediation_steps=[
                    "Review project description section",
                    "Ensure population characteristics are detailed",
                ],
            ),
            ComplianceChecklistItem(
                item_id="02_goals_objectives",
                category="Goals and Objectives",
                description="SMART goals and measurable objectives defined",
                is_complete=False,
                risk_level=RiskLevelEnum.YELLOW,
                remediation_steps=[
                    "Define specific, measurable outcomes",
                    "Align with funder requirements",
                ],
            ),
            ComplianceChecklistItem(
                item_id="03_evaluation_plan",
                category="Evaluation",
                description="Comprehensive evaluation methodology included",
                is_complete=False,
                risk_level=RiskLevelEnum.RED,
                remediation_steps=[
                    "Develop evaluation framework",
                    "Identify key performance indicators",
                ],
            ),
            ComplianceChecklistItem(
                item_id="04_budget_narrative",
                category="Budget",
                description="Detailed budget narrative aligned with project",
                is_complete=False,
                risk_level=RiskLevelEnum.YELLOW,
            ),
            ComplianceChecklistItem(
                item_id="05_org_capacity",
                category="Organizational Capacity",
                description="Organization demonstrates capacity to execute",
                is_complete=False,
                risk_level=RiskLevelEnum.GREEN,
            ),
        ]

        logger.info(f"Generated compliance checklist for plan {plan_id}")

        return checklist
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving compliance checklist: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve compliance checklist",
        )


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================


@router.get(
    "/{plan_id}/export",
    summary="Export plan as DOCX or JSON",
    status_code=status.HTTP_200_OK,
)
async def export_plan(
    plan_id: UUID,
    format: str = Query("json", regex="^(json|docx)$", description="Export format"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Export a grant plan in JSON or DOCX format.

    Args:
        plan_id: The plan UUID.
        format: Export format (json or docx).
        db: Database session.

    Returns:
        Dict: Exported plan data.

    Raises:
        HTTPException: If plan not found.
    """
    try:
        plan = await db.get(GrantPlan, str(plan_id))
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        # Load sections
        await db.refresh(plan, ["sections"])

        # Build export data
        export_data = {
            "plan_id": str(plan.id),
            "rfp_id": str(plan.rfp_id),
            "title": plan.title,
            "status": plan.status.value,
            "compliance_score": plan.compliance_score,
            "created_at": plan.created_at.isoformat(),
            "sections": [
                {
                    "title": sec.section_title,
                    "order": sec.section_order,
                    "content": sec.suggested_content,
                    "word_limit": sec.word_limit,
                    "word_count_target": sec.word_count_target,
                    "compliance_status": sec.compliance_status,
                }
                for sec in plan.sections
            ],
        }

        logger.info(f"Exported plan {plan_id} as {format}")

        if format == "docx":
            return {
                "format": "docx",
                "filename": f"GrantPlan_{plan.id}.docx",
                "data": export_data,
            }
        else:
            return export_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export plan",
        )


# ============================================================================
# DELETE ENDPOINT
# ============================================================================


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a plan",
)
async def delete_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a grant plan.

    Args:
        plan_id: The plan UUID.
        db: Database session.

    Raises:
        HTTPException: If plan not found.
    """
    try:
        plan = await db.get(GrantPlan, str(plan_id))
        if not plan:
            logger.warning(f"Plan not found: {plan_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        await db.delete(plan)
        await db.commit()

        # Log audit
        await log_audit(
            db,
            ActionTypeEnum.DELETE,
            "GrantPlan",
            str(plan.id),
            old_value={"title": plan.title},
        )
        await db.commit()

        logger.info(f"Deleted plan: {plan_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting plan: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete plan",
        )
