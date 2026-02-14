"""
RFP Upload and Parsing Routes - Module 2

Routes for uploading, parsing, and managing Request for Proposal documents.
Integrates with RFPParserService for automated parsing and requirement extraction.
"""

import logging
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models import RFP, RFPRequirement, RFPStatusEnum, ActionTypeEnum, AuditLog, User
from schemas import (
    RFPCreate,
    RFPRead,
    RFPListRead,
    RFPRequirementRead,
    RFPUpdate,
    PaginatedResponse,
)
from config import settings

from services import RFPParserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rfp", tags=["rfp"])


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
    """
    Log an action to the audit trail.

    Args:
        db: Database session.
        action: Action type.
        entity_type: Type of entity.
        entity_id: Entity ID.
        old_value: Old values.
        new_value: New values.
    """
    audit_log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
    )
    db.add(audit_log)


def get_allowed_extension(filename: str) -> Optional[str]:
    """Check if file extension is allowed and return it."""
    if "." not in filename:
        return None

    ext = "." + filename.rsplit(".", 1)[1].lower()
    if ext in settings.allowed_file_types:
        return ext
    return None


# ============================================================================
# UPLOAD & PARSING ENDPOINTS
# ============================================================================


@router.post(
    "/upload",
    response_model=RFPRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse RFP document",
)
async def upload_rfp(
    file: UploadFile = File(..., description="RFP document (PDF, DOCX, DOC, TXT)"),
    title: Optional[str] = Query(None, description="RFP title"),
    funder_name: Optional[str] = Query(None, description="Funder organization name"),
    deadline: Optional[str] = Query(None, description="Application deadline (ISO format)"),
    funding_amount: Optional[float] = Query(None, ge=0, description="Funding amount"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RFPRead:
    """
    Upload an RFP document for parsing.

    The endpoint will:
    1. Validate file type and size
    2. Save file to configured upload directory
    3. Trigger RFP parsing service
    4. Create RFP and RFPRequirement records
    5. Return parsed results

    Args:
        file: RFP document file.
        title: Optional RFP title.
        funder_name: Optional funder name.
        deadline: Optional deadline.
        funding_amount: Optional funding amount.
        db: Database session.

    Returns:
        RFPRead: Created RFP with parsed requirements.

    Raises:
        HTTPException: If file validation fails or parsing errors occur.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided",
            )

        ext = get_allowed_extension(file.filename)
        if not ext:
            logger.warning(f"Invalid file type: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.allowed_file_types)}",
            )

        # Check file size
        file_content = await file.read()
        if len(file_content) > settings.UPLOAD_MAX_FILE_SIZE:
            logger.warning(f"File too large: {len(file_content)} bytes")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds maximum allowed",
            )

        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

        # Save file
        file_path = os.path.join(settings.UPLOAD_DIR, f"{datetime.utcnow().timestamp()}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(file_content)

        logger.info(f"File saved to {file_path}")

        # Create RFP record
        rfp = RFP(
            title=title or file.filename,
            funder_name=funder_name or "Unknown",
            file_path=file_path,
            file_type=ext.lstrip("."),
            status=RFPStatusEnum.UPLOADED,
            raw_text=None,
        )

        if deadline:
            try:
                rfp.deadline = datetime.fromisoformat(deadline)
            except ValueError:
                logger.warning(f"Invalid deadline format: {deadline}")

        if funding_amount:
            rfp.funding_amount = funding_amount

        db.add(rfp)
        await db.flush()

        rfp.status = RFPStatusEnum.PARSING
        await db.commit()
        await db.refresh(rfp)

        # Parse the RFP document using RFPParserService
        try:
            parser = RFPParserService()
            parsed = await parser.parse_document(file_content, ext.lstrip("."), file.filename)

            # Update RFP with parsed data
            rfp.raw_text = parsed.raw_text[:50000] if parsed.raw_text else None
            if parsed.title and parsed.title != file.filename:
                rfp.title = title or parsed.title
            if parsed.funder_name and parsed.funder_name != "Unknown" and funder_name is None:
                rfp.funder_name = parsed.funder_name
            if parsed.deadline and not deadline:
                try:
                    rfp.deadline = datetime.fromisoformat(parsed.deadline)
                except (ValueError, TypeError):
                    pass
            if parsed.eligibility:
                rfp.eligibility_notes = "; ".join(parsed.eligibility)
            rfp.parsed_at = datetime.utcnow()

            # Create RFPRequirement records from parsed sections
            for i, section in enumerate(parsed.sections):
                req = RFPRequirement(
                    rfp_id=rfp.id,
                    section_name=section.name,
                    description=section.content[:2000] if section.content else section.name,
                    word_limit=section.word_limit,
                    scoring_weight=section.scoring_weight,
                    formatting_notes=section.formatting_notes,
                    required_attachments=[],
                    section_order=i,
                )
                db.add(req)

            rfp.status = RFPStatusEnum.PARSED
            logger.info(f"Successfully parsed RFP {rfp.id}: {len(parsed.sections)} sections extracted")
        except Exception as parse_err:
            logger.warning(f"RFP parsing failed for {rfp.id}, marking as uploaded: {parse_err}")
            rfp.status = RFPStatusEnum.UPLOADED

        await db.commit()
        await db.refresh(rfp)

        # Log audit event
        await log_audit(
            db,
            ActionTypeEnum.CREATE,
            "RFP",
            str(rfp.id),
            new_value={"title": rfp.title, "funder_name": rfp.funder_name, "status": rfp.status.value},
        )
        await db.commit()

        logger.info(f"Created RFP: {rfp.id} ({rfp.title})")

        return RFPRead.from_orm(rfp)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading RFP: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload RFP",
        )


# ============================================================================
# LIST & RETRIEVE ENDPOINTS
# ============================================================================


@router.get(
    "/",
    response_model=PaginatedResponse[RFPListRead],
    summary="List all RFPs",
    status_code=status.HTTP_200_OK,
)
async def list_rfps(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Items to return"),
    status_filter: Optional[RFPStatusEnum] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[RFPListRead]:
    """
    List all RFPs with optional status filtering.

    Args:
        skip: Pagination offset.
        limit: Pagination limit.
        status_filter: Filter by RFP status.
        db: Database session.

    Returns:
        PaginatedResponse: Paginated list of RFPs.
    """
    try:
        filters = []
        if status_filter:
            filters.append(RFP.status == status_filter)

        # Get total count
        count_query = select(func.count()).select_from(RFP)
        if filters:
            count_query = count_query.where(*filters)
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Fetch RFPs
        query = select(RFP).order_by(RFP.created_at.desc())
        if filters:
            query = query.where(*filters)

        result = await db.execute(query.offset(skip).limit(limit))
        rfps = result.scalars().all()

        logger.info(f"Retrieved {len(rfps)} RFPs (skip={skip}, limit={limit})")

        return PaginatedResponse(
            total=total,
            skip=skip,
            limit=limit,
            items=[RFPListRead.from_orm(rfp) for rfp in rfps],
        )
    except Exception as e:
        logger.error(f"Error listing RFPs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve RFPs",
        )


@router.get(
    "/{rfp_id}",
    response_model=RFPRead,
    summary="Get RFP details with parsed requirements",
    status_code=status.HTTP_200_OK,
)
async def get_rfp(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RFPRead:
    """
    Retrieve a single RFP with its parsed requirements.

    Args:
        rfp_id: The RFP UUID.
        db: Database session.

    Returns:
        RFPRead: The RFP details.

    Raises:
        HTTPException: If RFP not found.
    """
    try:
        result = await db.execute(
            select(RFP).where(RFP.id == rfp_id)
        )
        rfp = result.scalar_one_or_none()

        if not rfp:
            logger.warning(f"RFP not found: {rfp_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFP not found",
            )

        logger.info(f"Retrieved RFP: {rfp_id}")

        return RFPRead.from_orm(rfp)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving RFP: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve RFP",
        )


# ============================================================================
# REQUIREMENT ENDPOINTS
# ============================================================================


@router.get(
    "/{rfp_id}/requirements",
    response_model=List[RFPRequirementRead],
    summary="Get parsed requirements for an RFP",
    status_code=status.HTTP_200_OK,
)
async def get_rfp_requirements(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[RFPRequirementRead]:
    """
    Retrieve all parsed requirements for an RFP.

    Args:
        rfp_id: The RFP UUID.
        db: Database session.

    Returns:
        List[RFPRequirementRead]: Parsed requirements.

    Raises:
        HTTPException: If RFP not found.
    """
    try:
        # Verify RFP exists
        rfp = await db.get(RFP, str(rfp_id))
        if not rfp:
            logger.warning(f"RFP not found: {rfp_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFP not found",
            )

        # Get requirements
        result = await db.execute(
            select(RFPRequirement)
            .where(RFPRequirement.rfp_id == rfp_id)
            .order_by(RFPRequirement.section_order, RFPRequirement.section_name)
        )
        requirements = result.scalars().all()

        logger.info(f"Retrieved {len(requirements)} requirements for RFP {rfp_id}")

        return [RFPRequirementRead.from_orm(req) for req in requirements]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving requirements: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve requirements",
        )


@router.put(
    "/{rfp_id}/requirements/{req_id}",
    response_model=RFPRequirementRead,
    status_code=status.HTTP_200_OK,
    summary="Edit a parsed requirement manually",
)
async def update_requirement(
    rfp_id: UUID,
    req_id: UUID,
    req_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RFPRequirementRead:
    """
    Manually edit a parsed requirement.

    Args:
        rfp_id: The RFP UUID.
        req_id: The requirement UUID.
        req_data: Updated requirement data.
        db: Database session.

    Returns:
        RFPRequirementRead: Updated requirement.

    Raises:
        HTTPException: If requirement not found.
    """
    try:
        # Verify RFP exists
        rfp = await db.get(RFP, str(rfp_id))
        if not rfp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFP not found",
            )

        # Get requirement
        req = await db.get(RFPRequirement, str(req_id))
        if not req or req.rfp_id != rfp_id:
            logger.warning(f"Requirement not found: {req_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found",
            )

        # Store old values for audit
        old_value = {
            "section_name": req.section_name,
            "description": req.description,
            "word_limit": req.word_limit,
        }

        # Update fields
        for key, value in req_data.items():
            if hasattr(req, key):
                setattr(req, key, value)

        db.add(req)
        await db.commit()
        await db.refresh(req)

        # Log audit
        await log_audit(
            db,
            ActionTypeEnum.UPDATE,
            "RFPRequirement",
            str(req.id),
            old_value=old_value,
            new_value=req_data,
        )
        await db.commit()

        logger.info(f"Updated requirement: {req_id}")

        return RFPRequirementRead.from_orm(req)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating requirement: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update requirement",
        )


# ============================================================================
# RFP MANAGEMENT ENDPOINTS
# ============================================================================


@router.get(
    "/{rfp_id}/raw-text",
    response_model=Dict[str, str],
    summary="Get raw extracted text from RFP",
    status_code=status.HTTP_200_OK,
)
async def get_rfp_raw_text(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """
    Retrieve the raw extracted text from an RFP document.

    Args:
        rfp_id: The RFP UUID.
        db: Database session.

    Returns:
        Dict with raw_text field.

    Raises:
        HTTPException: If RFP not found.
    """
    try:
        rfp = await db.get(RFP, str(rfp_id))
        if not rfp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFP not found",
            )

        logger.info(f"Retrieved raw text for RFP {rfp_id}")

        return {
            "raw_text": rfp.raw_text or "No text available",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving raw text: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve raw text",
        )


@router.post(
    "/{rfp_id}/reparse",
    response_model=RFPRead,
    status_code=status.HTTP_200_OK,
    summary="Re-parse an existing RFP",
)
async def reparse_rfp(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RFPRead:
    """
    Trigger a re-parse of an existing RFP document.

    Args:
        rfp_id: The RFP UUID.
        db: Database session.

    Returns:
        RFPRead: Updated RFP.

    Raises:
        HTTPException: If RFP not found or parsing fails.
    """
    try:
        rfp = await db.get(RFP, str(rfp_id))
        if not rfp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFP not found",
            )

        # Check file exists
        if not os.path.exists(rfp.file_path):
            logger.error(f"RFP file not found: {rfp.file_path}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="RFP file not found",
            )

        # Update status
        rfp.status = RFPStatusEnum.PARSING
        db.add(rfp)
        await db.commit()
        await db.refresh(rfp)

        # TODO: Call RFPParserService to re-parse

        logger.info(f"Re-parsing RFP: {rfp_id}")

        return RFPRead.from_orm(rfp)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error re-parsing RFP: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to re-parse RFP",
        )


@router.delete(
    "/{rfp_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive an RFP",
)
async def archive_rfp(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Archive an RFP (soft delete).

    Args:
        rfp_id: The RFP UUID.
        db: Database session.

    Raises:
        HTTPException: If RFP not found.
    """
    try:
        rfp = await db.get(RFP, str(rfp_id))
        if not rfp:
            logger.warning(f"RFP not found: {rfp_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFP not found",
            )

        rfp.status = RFPStatusEnum.ARCHIVED
        db.add(rfp)
        await db.commit()

        # Log audit
        await log_audit(
            db,
            ActionTypeEnum.DELETE,
            "RFP",
            str(rfp.id),
            old_value={"status": "active"},
            new_value={"status": "archived"},
        )
        await db.commit()

        logger.info(f"Archived RFP: {rfp_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving RFP: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to archive RFP",
        )
