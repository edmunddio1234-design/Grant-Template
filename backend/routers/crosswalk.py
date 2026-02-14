"""
Crosswalk Mapping Routes - Module 3

Routes for generating, viewing, and managing crosswalk alignments between
RFP requirements and boilerplate sections.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models import (
    CrosswalkMap,
    RFP,
    RFPRequirement,
    BoilerplateSection,
    AlignmentScoreEnum,
    RiskLevelEnum,
    ActionTypeEnum,
    AuditLog,
    User,
)
from schemas import (
    CrosswalkMapRead,
    CrosswalkMapUpdate,
    CrosswalkResult,
    AlignmentMatrixRow,
    PaginatedResponse,
)

from services.crosswalk_engine import CrosswalkEngine, AlignmentLevel, RiskLevel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crosswalk", tags=["crosswalk"])


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
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Generate crosswalk for an RFP",
)
async def generate_crosswalk(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Generate a complete crosswalk alignment between RFP requirements and boilerplate.

    This endpoint:
    1. Fetches all parsed RFP requirements
    2. Fetches all active boilerplate sections
    3. Runs the CrosswalkEngine to generate alignments
    4. Saves results to the crosswalk_maps table
    5. Returns structured results

    Args:
        rfp_id: The RFP UUID.
        db: Database session.

    Returns:
        Dict with crosswalk generation results.

    Raises:
        HTTPException: If RFP not found or generation fails.
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

        # Get all requirements for this RFP
        req_result = await db.execute(
            select(RFPRequirement).where(RFPRequirement.rfp_id == rfp_id)
        )
        requirements = req_result.scalars().all()

        if not requirements:
            logger.warning(f"No requirements found for RFP {rfp_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No requirements found for this RFP",
            )

        # Get all active boilerplate sections
        sec_result = await db.execute(
            select(BoilerplateSection).where(BoilerplateSection.is_active == True)
        )
        sections = sec_result.scalars().all()

        # Build boilerplate data dict for the CrosswalkEngine
        boilerplate_for_engine = {}
        boilerplate_lookup = {}  # Map area/tag -> BoilerplateSection ORM object
        for bp in sections:
            area_key = (bp.category or bp.section_title or "general").lower().replace(" ", "_")
            boilerplate_for_engine[area_key] = {
                "name": bp.section_title,
                "content": bp.content or "",
                "tags": bp.tags if hasattr(bp, 'tags') and bp.tags else [area_key],
            }
            boilerplate_lookup[area_key] = bp

        # Initialize CrosswalkEngine with real boilerplate data (falls back to defaults if empty)
        engine = CrosswalkEngine(
            boilerplate_data=boilerplate_for_engine if boilerplate_for_engine else None,
            use_ml=True,
        )

        # Map alignment levels to DB enums
        level_map = {
            AlignmentLevel.STRONG: AlignmentScoreEnum.STRONG,
            AlignmentLevel.PARTIAL: AlignmentScoreEnum.PARTIAL,
            AlignmentLevel.WEAK: AlignmentScoreEnum.WEAK,
            AlignmentLevel.NONE: AlignmentScoreEnum.NONE,
        }
        risk_map = {
            RiskLevel.GREEN: RiskLevelEnum.GREEN,
            RiskLevel.YELLOW: RiskLevelEnum.YELLOW,
            RiskLevel.RED: RiskLevelEnum.RED,
        }

        mappings_created = 0
        auto_matches = 0
        gaps_found = 0

        # Run the real engine for each requirement against all boilerplate
        for requirement in requirements:
            req_text = f"{requirement.section_name}: {requirement.description}"

            # Identify matching organizational areas via the engine
            matching_areas = engine._identify_matching_areas(req_text)

            if matching_areas and sections:
                # For each matching area, find the best boilerplate section
                best_score = 0.0
                best_bp = None
                best_level = AlignmentLevel.NONE
                best_risk = RiskLevel.YELLOW

                for org_area, strength in matching_areas.items():
                    bp_data = engine._get_boilerplate_for_area(org_area, None)
                    if bp_data:
                        similarity = engine._compute_similarity(req_text, bp_data["content"])
                        tag_match = engine._match_tags(req_text, bp_data.get("tags", []))
                        score, level = engine._score_alignment(similarity, tag_match)
                        risk = engine._assess_risk(level, requirement.scoring_weight or 0.5)

                        if score > best_score:
                            best_score = score
                            best_level = level
                            best_risk = risk
                            # Try to find matching ORM boilerplate
                            best_bp = boilerplate_lookup.get(org_area) or (sections[0] if sections else None)

                if best_bp:
                    # Check for existing mapping
                    existing = await db.execute(
                        select(CrosswalkMap).where(
                            and_(
                                CrosswalkMap.rfp_requirement_id == requirement.id,
                                CrosswalkMap.boilerplate_section_id == best_bp.id,
                            )
                        )
                    )
                    if not existing.scalar_one_or_none():
                        gap = best_level in (AlignmentLevel.NONE, AlignmentLevel.WEAK)
                        mapping = CrosswalkMap(
                            rfp_requirement_id=requirement.id,
                            boilerplate_section_id=best_bp.id,
                            alignment_score=level_map.get(best_level, AlignmentScoreEnum.PARTIAL),
                            gap_flag=gap,
                            risk_level=risk_map.get(best_risk, RiskLevelEnum.YELLOW),
                            auto_matched=True,
                            customization_needed=(best_level != AlignmentLevel.STRONG),
                        )
                        db.add(mapping)
                        mappings_created += 1
                        auto_matches += 1
                        if gap:
                            gaps_found += 1
            else:
                # No keyword match — flag as gap, link to first boilerplate section if available
                if sections:
                    existing = await db.execute(
                        select(CrosswalkMap).where(
                            and_(
                                CrosswalkMap.rfp_requirement_id == requirement.id,
                                CrosswalkMap.boilerplate_section_id == sections[0].id,
                            )
                        )
                    )
                    if not existing.scalar_one_or_none():
                        mapping = CrosswalkMap(
                            rfp_requirement_id=requirement.id,
                            boilerplate_section_id=sections[0].id,
                            alignment_score=AlignmentScoreEnum.NONE,
                            gap_flag=True,
                            risk_level=RiskLevelEnum.RED,
                            auto_matched=True,
                            customization_needed=True,
                        )
                        db.add(mapping)
                        mappings_created += 1
                        gaps_found += 1

        await db.commit()

        logger.info(f"Generated {mappings_created} crosswalk mappings for RFP {rfp_id}")

        return {
            "rfp_id": str(rfp_id),
            "mappings_created": mappings_created,
            "auto_matches": auto_matches,
            "gaps_found": gaps_found,
            "manual_reviews_needed": len(requirements) - auto_matches,
            "engine": "CrosswalkEngine (TF-IDF + keyword)",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating crosswalk: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate crosswalk",
        )


# ============================================================================
# RETRIEVE ENDPOINTS
# ============================================================================


@router.get(
    "/{rfp_id}",
    response_model=PaginatedResponse[CrosswalkResult],
    summary="Get crosswalk results for an RFP",
    status_code=status.HTTP_200_OK,
)
async def get_crosswalk(
    rfp_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[CrosswalkResult]:
    """
    Retrieve crosswalk mapping results for an RFP.

    Args:
        rfp_id: The RFP UUID.
        skip: Pagination offset.
        limit: Pagination limit.
        db: Database session.

    Returns:
        PaginatedResponse: Paginated crosswalk results.

    Raises:
        HTTPException: If RFP not found.
    """
    try:
        # Verify RFP exists
        rfp = await db.get(RFP, str(rfp_id))
        if not rfp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFP not found",
            )

        # Count total mappings
        count_result = await db.execute(
            select(func.count(CrosswalkMap.id)).where(
                CrosswalkMap.rfp_requirement_id.in_(
                    select(RFPRequirement.id).where(RFPRequirement.rfp_id == rfp_id)
                )
            )
        )
        total = count_result.scalar() or 0

        # Get mappings with related data
        result = await db.execute(
            select(CrosswalkMap)
            .join(RFPRequirement)
            .where(RFPRequirement.rfp_id == rfp_id)
            .offset(skip)
            .limit(limit)
        )
        mappings = result.scalars().all()

        # Build results with full details
        results = []
        for mapping in mappings:
            req = await db.get(RFPRequirement, str(mapping.rfp_requirement_id))
            section = await db.get(BoilerplateSection, str(mapping.boilerplate_section_id))

            if req and section:
                results.append(
                    CrosswalkResult(
                        rfp_requirement=req,
                        boilerplate_section=section,
                        alignment_score=mapping.alignment_score,
                        risk_level=mapping.risk_level,
                        gap_flag=mapping.gap_flag,
                        customization_needed=mapping.customization_needed,
                        notes=mapping.notes,
                    )
                )

        logger.info(f"Retrieved {len(results)} crosswalk mappings for RFP {rfp_id}")

        return PaginatedResponse(
            total=total,
            skip=skip,
            limit=limit,
            items=results,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving crosswalk: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve crosswalk",
        )


@router.get(
    "/{rfp_id}/matrix",
    response_model=List[AlignmentMatrixRow],
    summary="Get alignment matrix for dashboard display",
    status_code=status.HTTP_200_OK,
)
async def get_alignment_matrix(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[AlignmentMatrixRow]:
    """
    Get alignment matrix formatted for side-by-side display.

    Args:
        rfp_id: The RFP UUID.
        db: Database session.

    Returns:
        List[AlignmentMatrixRow]: Alignment matrix rows.

    Raises:
        HTTPException: If RFP not found.
    """
    try:
        # Verify RFP exists
        rfp = await db.get(RFP, str(rfp_id))
        if not rfp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFP not found",
            )

        # Get all mappings for RFP
        result = await db.execute(
            select(CrosswalkMap)
            .join(RFPRequirement)
            .where(RFPRequirement.rfp_id == rfp_id)
            .order_by(RFPRequirement.section_order, RFPRequirement.section_name)
        )
        mappings = result.scalars().all()

        matrix_rows = []
        for mapping in mappings:
            req = await db.get(RFPRequirement, str(mapping.rfp_requirement_id))
            section = await db.get(BoilerplateSection, str(mapping.boilerplate_section_id))

            if req and section:
                row = AlignmentMatrixRow(
                    requirement_id=req.id,
                    requirement_title=req.section_name,
                    boilerplate_id=section.id,
                    boilerplate_title=section.section_title,
                    alignment_score=mapping.alignment_score,
                    risk_level=mapping.risk_level,
                    word_limit=req.word_limit,
                    gap_flag=mapping.gap_flag,
                    customization_needed=mapping.customization_needed,
                )
                matrix_rows.append(row)

        logger.info(f"Generated alignment matrix with {len(matrix_rows)} rows for RFP {rfp_id}")

        return matrix_rows
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating alignment matrix: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate alignment matrix",
        )


# ============================================================================
# UPDATE ENDPOINTS
# ============================================================================


@router.put(
    "/map/{map_id}",
    response_model=CrosswalkMapRead,
    status_code=status.HTTP_200_OK,
    summary="Update a crosswalk mapping manually",
)
async def update_crosswalk_map(
    map_id: UUID,
    update_data: CrosswalkMapUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CrosswalkMapRead:
    """
    Manually update a crosswalk mapping.

    Args:
        map_id: The crosswalk map UUID.
        update_data: Update payload.
        db: Database session.

    Returns:
        CrosswalkMapRead: Updated mapping.

    Raises:
        HTTPException: If mapping not found.
    """
    try:
        mapping = await db.get(CrosswalkMap, str(map_id))
        if not mapping:
            logger.warning(f"Crosswalk map not found: {map_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crosswalk mapping not found",
            )

        # Store old values
        old_value = {
            "alignment_score": mapping.alignment_score.value,
            "risk_level": mapping.risk_level.value,
            "gap_flag": mapping.gap_flag,
        }

        # Apply updates
        update_fields = update_data.model_dump(exclude_unset=True)
        for key, value in update_fields.items():
            setattr(mapping, key, value)

        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)

        # Log audit
        await log_audit(
            db,
            ActionTypeEnum.UPDATE,
            "CrosswalkMap",
            str(mapping.id),
            old_value=old_value,
            new_value=update_fields,
        )
        await db.commit()

        logger.info(f"Updated crosswalk map: {map_id}")

        return CrosswalkMapRead.from_orm(mapping)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating crosswalk map: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update crosswalk mapping",
        )


@router.post(
    "/map/{map_id}/approve",
    response_model=CrosswalkMapRead,
    status_code=status.HTTP_200_OK,
    summary="Mark a mapping as reviewer-approved",
)
async def approve_crosswalk_map(
    map_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CrosswalkMapRead:
    """
    Mark a crosswalk mapping as approved by reviewer.

    Args:
        map_id: The crosswalk map UUID.
        db: Database session.

    Returns:
        CrosswalkMapRead: Updated mapping.

    Raises:
        HTTPException: If mapping not found.
    """
    try:
        mapping = await db.get(CrosswalkMap, str(map_id))
        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crosswalk mapping not found",
            )

        mapping.reviewer_approved = True
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)

        # Log audit
        await log_audit(
            db,
            ActionTypeEnum.APPROVE,
            "CrosswalkMap",
            str(mapping.id),
            new_value={"reviewer_approved": True},
        )
        await db.commit()

        logger.info(f"Approved crosswalk map: {map_id}")

        return CrosswalkMapRead.from_orm(mapping)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving crosswalk map: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve crosswalk mapping",
        )


# ============================================================================
# REGENERATE ENDPOINTS
# ============================================================================


@router.post(
    "/{rfp_id}/regenerate",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Regenerate crosswalk for an RFP",
)
async def regenerate_crosswalk(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Regenerate crosswalk alignment (clears and recreates all mappings).

    Args:
        rfp_id: The RFP UUID.
        db: Database session.

    Returns:
        Dict: Regeneration results.

    Raises:
        HTTPException: If RFP not found.
    """
    try:
        # Verify RFP exists
        rfp = await db.get(RFP, str(rfp_id))
        if not rfp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFP not found",
            )

        # Delete existing crosswalk maps
        await db.execute(
            select(CrosswalkMap)
            .where(
                CrosswalkMap.rfp_requirement_id.in_(
                    select(RFPRequirement.id).where(RFPRequirement.rfp_id == rfp_id)
                )
            )
        )
        await db.commit()

        # Generate new crosswalk
        return await generate_crosswalk(rfp_id, current_user, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating crosswalk: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate crosswalk",
        )


# ============================================================================
# EXPORT & SUMMARY ENDPOINTS
# ============================================================================


@router.get(
    "/{rfp_id}/export",
    response_model=Dict[str, Any],
    summary="Export crosswalk as CSV or JSON",
    status_code=status.HTTP_200_OK,
)
async def export_crosswalk(
    rfp_id: UUID,
    format: str = Query("json", regex="^(csv|json)$", description="Export format"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Export crosswalk results in JSON or CSV format.

    Args:
        rfp_id: The RFP UUID.
        format: Export format (json or csv).
        db: Database session.

    Returns:
        Dict: Exported crosswalk data.

    Raises:
        HTTPException: If RFP not found.
    """
    try:
        # Verify RFP exists
        rfp = await db.get(RFP, str(rfp_id))
        if not rfp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFP not found",
            )

        # Get mappings
        result = await db.execute(
            select(CrosswalkMap)
            .join(RFPRequirement)
            .where(RFPRequirement.rfp_id == rfp_id)
        )
        mappings = result.scalars().all()

        # Build export data
        rows = []
        for mapping in mappings:
            req = await db.get(RFPRequirement, str(mapping.rfp_requirement_id))
            section = await db.get(BoilerplateSection, str(mapping.boilerplate_section_id))

            if req and section:
                row = {
                    "requirement": req.section_name,
                    "boilerplate": section.section_title,
                    "alignment_score": mapping.alignment_score.value,
                    "risk_level": mapping.risk_level.value,
                    "gap_flag": mapping.gap_flag,
                    "customization_needed": mapping.customization_needed,
                }
                rows.append(row)

        logger.info(f"Exported crosswalk with {len(rows)} mappings for RFP {rfp_id}")

        if format == "csv":
            # Return CSV format
            return {
                "format": "csv",
                "filename": f"crosswalk_{rfp_id}.csv",
                "data": rows,
            }
        else:
            # Return JSON format
            return {
                "format": "json",
                "rfp_id": str(rfp_id),
                "rfp_title": rfp.title,
                "export_date": datetime.utcnow().isoformat(),
                "mappings": rows,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting crosswalk: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export crosswalk",
        )


@router.get(
    "/{rfp_id}/summary",
    response_model=Dict[str, Any],
    summary="Get crosswalk summary statistics",
    status_code=status.HTTP_200_OK,
)
async def get_crosswalk_summary(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get summary statistics for a crosswalk.

    Args:
        rfp_id: The RFP UUID.
        db: Database session.

    Returns:
        Dict: Summary statistics.

    Raises:
        HTTPException: If RFP not found.
    """
    try:
        # Verify RFP exists
        rfp = await db.get(RFP, str(rfp_id))
        if not rfp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFP not found",
            )

        # Get mappings
        result = await db.execute(
            select(CrosswalkMap)
            .join(RFPRequirement)
            .where(RFPRequirement.rfp_id == rfp_id)
        )
        mappings = result.scalars().all()

        # Calculate statistics
        strong_count = sum(1 for m in mappings if m.alignment_score == AlignmentScoreEnum.STRONG)
        partial_count = sum(1 for m in mappings if m.alignment_score == AlignmentScoreEnum.PARTIAL)
        weak_count = sum(1 for m in mappings if m.alignment_score == AlignmentScoreEnum.WEAK)
        none_count = sum(1 for m in mappings if m.alignment_score == AlignmentScoreEnum.NONE)

        red_count = sum(1 for m in mappings if m.risk_level == RiskLevelEnum.RED)
        yellow_count = sum(1 for m in mappings if m.risk_level == RiskLevelEnum.YELLOW)
        green_count = sum(1 for m in mappings if m.risk_level == RiskLevelEnum.GREEN)

        gaps = sum(1 for m in mappings if m.gap_flag)
        customization_needed = sum(1 for m in mappings if m.customization_needed)

        alignment_percentage = (
            (strong_count * 100 + partial_count * 50) / len(mappings) if mappings else 0
        )

        logger.info(f"Generated summary for RFP {rfp_id}")

        return {
            "rfp_id": str(rfp_id),
            "total_mappings": len(mappings),
            "alignment_scores": {
                "strong": strong_count,
                "partial": partial_count,
                "weak": weak_count,
                "none": none_count,
            },
            "risk_levels": {
                "red": red_count,
                "yellow": yellow_count,
                "green": green_count,
            },
            "gaps_identified": gaps,
            "customization_needed": customization_needed,
            "overall_alignment_percentage": round(alignment_percentage, 2),
            "overall_risk_level": "red" if red_count > 0 else "yellow" if yellow_count > 0 else "green",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating crosswalk summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate crosswalk summary",
        )
