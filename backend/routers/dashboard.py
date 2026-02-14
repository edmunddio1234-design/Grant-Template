"""
Gap Analysis & Risk Dashboard Routes - Module 5

Routes for dashboard analytics, gap analysis visualization, risk assessment,
and recommendation prioritization.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models import (
    RFP,
    GapAnalysis,
    GrantPlan,
    CrosswalkMap,
    RFPRequirement,
    RiskLevelEnum,
    RFPStatusEnum,
    AlignmentScoreEnum,
    GrantPlanStatusEnum,
    User,
)
from schemas import (
    GapAnalysisRead,
    RiskDashboardSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


# ============================================================================
# OVERVIEW & SUMMARY ENDPOINTS
# ============================================================================


@router.get(
    "/{rfp_id}/overview",
    response_model=Dict[str, Any],
    summary="Get overall risk dashboard for an RFP",
    status_code=status.HTTP_200_OK,
)
async def get_rfp_dashboard_overview(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get comprehensive risk dashboard overview for an RFP.

    Args:
        rfp_id: The RFP UUID.
        db: Database session.

    Returns:
        Dict: Dashboard overview with risk metrics.

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

        # Get crosswalk mappings
        mappings_result = await db.execute(
            select(CrosswalkMap)
            .join(RFPRequirement)
            .where(RFPRequirement.rfp_id == rfp_id)
        )
        mappings = mappings_result.scalars().all()

        # Get gap analysis
        gap_result = await db.execute(
            select(GapAnalysis)
            .where(GapAnalysis.rfp_id == rfp_id)
            .order_by(GapAnalysis.analysis_date.desc())
        )
        latest_gap = gap_result.scalars().first()

        # Calculate risk metrics
        red_count = sum(1 for m in mappings if m.risk_level == RiskLevelEnum.RED)
        yellow_count = sum(1 for m in mappings if m.risk_level == RiskLevelEnum.YELLOW)
        green_count = sum(1 for m in mappings if m.risk_level == RiskLevelEnum.GREEN)

        gaps_count = sum(1 for m in mappings if m.gap_flag)
        customization_count = sum(1 for m in mappings if m.customization_needed)

        overall_risk = "red" if red_count > 0 else "yellow" if yellow_count > 0 else "green"

        dashboard = {
            "rfp_id": str(rfp_id),
            "rfp_title": rfp.title,
            "rfp_funder": rfp.funder_name,
            "rfp_status": rfp.status.value,
            "rfp_deadline": rfp.deadline.isoformat() if rfp.deadline else None,
            "total_requirements": len(mappings),
            "risk_metrics": {
                "red": red_count,
                "yellow": yellow_count,
                "green": green_count,
                "overall_level": overall_risk,
            },
            "gaps": {
                "identified": gaps_count,
                "customization_needed": customization_count,
            },
            "latest_gap_analysis": latest_gap.analysis_date.isoformat() if latest_gap else None,
            "overall_gap_level": latest_gap.overall_risk_level.value if latest_gap else "unknown",
            "recommendations_count": len(latest_gap.recommendations) if latest_gap else 0,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Generated dashboard overview for RFP {rfp_id}")

        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating dashboard overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dashboard overview",
        )


@router.get(
    "/summary",
    response_model=RiskDashboardSummary,
    summary="Get summary across all active RFPs",
    status_code=status.HTTP_200_OK,
)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RiskDashboardSummary:
    """
    Get high-level dashboard summary across all active RFPs.

    Args:
        db: Database session.

    Returns:
        RiskDashboardSummary: Aggregated dashboard metrics.
    """
    try:
        # Get all active RFPs
        rfp_result = await db.execute(
            select(RFP).where(RFP.status != RFPStatusEnum.ARCHIVED)
        )
        rfps = rfp_result.scalars().all()

        # Count RFPs by risk level
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0

        for rfp in rfps:
            mappings_result = await db.execute(
                select(CrosswalkMap)
                .join(RFPRequirement)
                .where(RFPRequirement.rfp_id == rfp.id)
            )
            mappings = mappings_result.scalars().all()

            red_count = sum(1 for m in mappings if m.risk_level == RiskLevelEnum.RED)
            yellow_count = sum(1 for m in mappings if m.risk_level == RiskLevelEnum.YELLOW)

            if red_count > 0:
                high_risk_count += 1
            elif yellow_count > 0:
                medium_risk_count += 1
            else:
                low_risk_count += 1

        # Get grant plans
        plans_result = await db.execute(
            select(GrantPlan).where(
                GrantPlan.status.in_([
                    GrantPlanStatusEnum.DRAFT,
                    GrantPlanStatusEnum.REVIEW,
                ])
            )
        )
        plans = plans_result.scalars().all()

        # Calculate average compliance score
        avg_compliance = 0.0
        if plans:
            scores = [p.compliance_score for p in plans if p.compliance_score]
            avg_compliance = sum(scores) / len(scores) if scores else 0.0

        # Upcoming deadlines
        today = datetime.utcnow()
        upcoming = [
            {
                "rfp_title": rfp.title,
                "deadline": rfp.deadline.isoformat() if rfp.deadline else None,
                "days_remaining": (rfp.deadline - today).days if rfp.deadline else None,
            }
            for rfp in rfps
            if rfp.deadline and rfp.deadline > today and (rfp.deadline - today).days <= 30
        ]

        # Count gaps requiring attention (can't use await in generator)
        total_gaps = 0
        for rfp in rfps:
            gap_result = await db.execute(
                select(func.count(CrosswalkMap.id))
                .join(RFPRequirement)
                .where(
                    and_(
                        RFPRequirement.rfp_id == rfp.id,
                        CrosswalkMap.gap_flag == True,
                    )
                )
            )
            total_gaps += gap_result.scalar() or 0

        summary = RiskDashboardSummary(
            total_rfps=len(rfps),
            high_risk_count=high_risk_count,
            medium_risk_count=medium_risk_count,
            low_risk_count=low_risk_count,
            average_compliance_score=round(avg_compliance, 2),
            gaps_requiring_attention=total_gaps,
            plans_in_progress=len(plans),
            upcoming_deadlines=upcoming,
        )

        logger.info(f"Generated dashboard summary: {len(rfps)} RFPs, {high_risk_count} high-risk")

        return summary
    except Exception as e:
        logger.error(f"Error generating dashboard summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dashboard summary",
        )


# ============================================================================
# FUNDER BREAKDOWN ENDPOINT
# ============================================================================


@router.get(
    "/summary/funder-breakdown",
    response_model=Dict[str, Any],
    summary="Get grant metrics aggregated by funder",
    status_code=status.HTTP_200_OK,
)
async def get_funder_breakdown(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get grant funder metrics aggregated by funding type and funder name.

    Returns awarded, pending, and denied totals grouped by funder,
    used by the Grant Funder Analytics chart on the dashboard.
    """
    try:
        # Get all RFPs grouped by funder
        result = await db.execute(
            select(
                RFP.funder_name,
                RFP.funding_type,
                RFP.funding_amount,
                RFP.status,
            ).order_by(RFP.funder_name)
        )
        rows = result.all()

        # Aggregate by funder name
        funder_map: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            name = row.funder_name or "Unknown"
            if name not in funder_map:
                funder_map[name] = {
                    "name": name,
                    "category": (row.funding_type.value if row.funding_type else "other").capitalize(),
                    "awarded": 0.0,
                    "pending": 0.0,
                    "denied": 0.0,
                }
            amount = row.funding_amount or 0.0
            status_val = row.status.value if row.status else "uploaded"

            # Map RFP status to grant outcome
            if status_val in ("analyzed", "archived"):
                funder_map[name]["awarded"] += amount
            elif status_val in ("uploaded", "parsing", "parsed"):
                funder_map[name]["pending"] += amount

        funders = list(funder_map.values())

        # Sort by total descending
        funders.sort(key=lambda f: f["awarded"] + f["pending"] + f["denied"], reverse=True)

        total_awarded = sum(f["awarded"] for f in funders)
        total_pending = sum(f["pending"] for f in funders)
        total_denied = sum(f["denied"] for f in funders)

        logger.info(f"Generated funder breakdown: {len(funders)} funders")

        return {
            "funders": funders,
            "summary": {
                "total_awarded": total_awarded,
                "total_pending": total_pending,
                "total_denied": total_denied,
                "total_pipeline": total_awarded + total_pending + total_denied,
                "funder_count": len(funders),
            },
        }
    except Exception as e:
        logger.error(f"Error generating funder breakdown: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate funder breakdown",
        )


# ============================================================================
# GAP ANALYSIS ENDPOINTS
# ============================================================================


@router.get(
    "/{rfp_id}/gaps",
    response_model=GapAnalysisRead,
    summary="Get detailed gap analysis for an RFP",
    status_code=status.HTTP_200_OK,
)
async def get_gap_analysis(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GapAnalysisRead:
    """
    Get detailed gap analysis results for an RFP.

    Args:
        rfp_id: The RFP UUID.
        db: Database session.

    Returns:
        GapAnalysisRead: Gap analysis details.

    Raises:
        HTTPException: If RFP or gap analysis not found.
    """
    try:
        # Verify RFP exists
        rfp = await db.get(RFP, str(rfp_id))
        if not rfp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFP not found",
            )

        # Get latest gap analysis
        result = await db.execute(
            select(GapAnalysis)
            .where(GapAnalysis.rfp_id == rfp_id)
            .order_by(GapAnalysis.analysis_date.desc())
        )
        gap_analysis = result.scalars().first()

        if not gap_analysis:
            logger.warning(f"Gap analysis not found for RFP {rfp_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gap analysis not found for this RFP",
            )

        logger.info(f"Retrieved gap analysis for RFP {rfp_id}")

        return GapAnalysisRead.from_orm(gap_analysis)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving gap analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve gap analysis",
        )


# ============================================================================
# RISK & SCORING ENDPOINTS
# ============================================================================


@router.get(
    "/{rfp_id}/risks",
    response_model=Dict[str, Any],
    summary="Get risk distribution data for charts",
    status_code=status.HTTP_200_OK,
)
async def get_risk_distribution(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get risk distribution metrics for dashboard visualization.

    Args:
        rfp_id: The RFP UUID.
        db: Database session.

    Returns:
        Dict: Risk distribution data.

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

        # Get crosswalk mappings
        mappings_result = await db.execute(
            select(CrosswalkMap)
            .join(RFPRequirement)
            .where(RFPRequirement.rfp_id == rfp_id)
        )
        mappings = mappings_result.scalars().all()

        # Calculate risk distribution
        risk_distribution = {
            "red": sum(1 for m in mappings if m.risk_level == RiskLevelEnum.RED),
            "yellow": sum(1 for m in mappings if m.risk_level == RiskLevelEnum.YELLOW),
            "green": sum(1 for m in mappings if m.risk_level == RiskLevelEnum.GREEN),
        }

        # Calculate alignment distribution
        alignment_distribution = {
            "strong": sum(1 for m in mappings if m.alignment_score == AlignmentScoreEnum.STRONG),
            "partial": sum(1 for m in mappings if m.alignment_score == AlignmentScoreEnum.PARTIAL),
            "weak": sum(1 for m in mappings if m.alignment_score == AlignmentScoreEnum.WEAK),
            "none": sum(1 for m in mappings if m.alignment_score == AlignmentScoreEnum.NONE),
        }

        total = len(mappings)

        logger.info(f"Generated risk distribution for RFP {rfp_id}")

        return {
            "rfp_id": str(rfp_id),
            "total_requirements": total,
            "risk_distribution": risk_distribution,
            "risk_distribution_percentage": {
                k: round((v / total * 100), 2) if total > 0 else 0
                for k, v in risk_distribution.items()
            },
            "alignment_distribution": alignment_distribution,
            "alignment_distribution_percentage": {
                k: round((v / total * 100), 2) if total > 0 else 0
                for k, v in alignment_distribution.items()
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating risk distribution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate risk distribution",
        )


@router.get(
    "/{rfp_id}/scores",
    response_model=Dict[str, Any],
    summary="Get alignment scores breakdown",
    status_code=status.HTTP_200_OK,
)
async def get_alignment_scores(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get alignment scores breakdown for an RFP.

    Args:
        rfp_id: The RFP UUID.
        db: Database session.

    Returns:
        Dict: Alignment score metrics.

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

        # Get crosswalk mappings
        mappings_result = await db.execute(
            select(CrosswalkMap)
            .join(RFPRequirement)
            .where(RFPRequirement.rfp_id == rfp_id)
        )
        mappings = mappings_result.scalars().all()

        # Calculate average alignment score
        alignment_values = {
            AlignmentScoreEnum.STRONG: 100,
            AlignmentScoreEnum.PARTIAL: 50,
            AlignmentScoreEnum.WEAK: 25,
            AlignmentScoreEnum.NONE: 0,
        }

        total_score = sum(alignment_values[m.alignment_score] for m in mappings)
        average_score = total_score / len(mappings) if mappings else 0

        # By category
        gap_count = sum(1 for m in mappings if m.gap_flag)
        customization_count = sum(1 for m in mappings if m.customization_needed)
        auto_matched = sum(1 for m in mappings if m.auto_matched)
        approved = sum(1 for m in mappings if m.reviewer_approved)

        logger.info(f"Generated alignment scores for RFP {rfp_id}")

        return {
            "rfp_id": str(rfp_id),
            "average_alignment_score": round(average_score, 2),
            "total_mappings": len(mappings),
            "gaps_identified": gap_count,
            "customization_needed": customization_count,
            "auto_matched_mappings": auto_matched,
            "reviewer_approved_mappings": approved,
            "manual_review_needed": len(mappings) - approved,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating alignment scores: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate alignment scores",
        )


# ============================================================================
# RECOMMENDATIONS ENDPOINT
# ============================================================================


@router.get(
    "/{rfp_id}/recommendations",
    response_model=List[Dict[str, Any]],
    summary="Get prioritized recommendations",
    status_code=status.HTTP_200_OK,
)
async def get_recommendations(
    rfp_id: UUID,
    priority: Optional[str] = Query(None, regex="^(high|medium|low)$", description="Filter by priority"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Get prioritized recommendations based on gap analysis.

    Args:
        rfp_id: The RFP UUID.
        priority: Optional priority filter (high/medium/low).
        db: Database session.

    Returns:
        List[Dict]: Prioritized recommendations.

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

        # Get latest gap analysis
        gap_result = await db.execute(
            select(GapAnalysis)
            .where(GapAnalysis.rfp_id == rfp_id)
            .order_by(GapAnalysis.analysis_date.desc())
        )
        gap_analysis = gap_result.scalars().first()

        recommendations = []

        if gap_analysis:
            # Build recommendations from gap analysis
            if gap_analysis.missing_metrics:
                for metric in gap_analysis.missing_metrics:
                    recommendations.append({
                        "id": f"rec_metric_{len(recommendations)}",
                        "priority": "high",
                        "category": "Metrics and Evaluation",
                        "description": f"Add data collection for: {metric}",
                        "action": f"Develop measurement strategy for {metric}",
                        "impact": "Improves evaluation rigor and grant competitiveness",
                    })

            if gap_analysis.weak_alignments:
                for alignment in gap_analysis.weak_alignments:
                    recommendations.append({
                        "id": f"rec_align_{len(recommendations)}",
                        "priority": "high",
                        "category": "Alignment",
                        "description": f"Strengthen alignment with requirement: {alignment}",
                        "action": "Review boilerplate and enhance content",
                        "impact": "Increases alignment score and reviewer confidence",
                    })

            if gap_analysis.evaluation_weaknesses:
                for weakness in gap_analysis.evaluation_weaknesses:
                    recommendations.append({
                        "id": f"rec_eval_{len(recommendations)}",
                        "priority": "medium",
                        "category": "Evaluation",
                        "description": f"Address evaluation weakness: {weakness}",
                        "action": "Enhance evaluation plan section",
                        "impact": "Demonstrates stronger program assessment capability",
                    })

            if gap_analysis.missing_partnerships:
                for partnership in gap_analysis.missing_partnerships:
                    recommendations.append({
                        "id": f"rec_partner_{len(recommendations)}",
                        "priority": "medium",
                        "category": "Partnerships",
                        "description": f"Develop partnership with: {partnership}",
                        "action": "Identify and formalize partnership",
                        "impact": "Enhances program capacity and sustainability",
                    })

        # Filter by priority if provided
        if priority:
            recommendations = [r for r in recommendations if r["priority"] == priority]

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))

        logger.info(f"Generated {len(recommendations)} recommendations for RFP {rfp_id}")

        return recommendations
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations",
        )


# ============================================================================
# TIMELINE ENDPOINT
# ============================================================================


@router.get(
    "/{rfp_id}/timeline",
    response_model=List[Dict[str, Any]],
    summary="Get risk trends over time",
    status_code=status.HTTP_200_OK,
)
async def get_risk_timeline(
    rfp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Get risk assessment trends over time if multiple analyses exist.

    Args:
        rfp_id: The RFP UUID.
        db: Database session.

    Returns:
        List[Dict]: Timeline of risk assessments.

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

        # Get all gap analyses ordered by date
        result = await db.execute(
            select(GapAnalysis)
            .where(GapAnalysis.rfp_id == rfp_id)
            .order_by(GapAnalysis.analysis_date.asc())
        )
        analyses = result.scalars().all()

        timeline = [
            {
                "date": analysis.analysis_date.isoformat(),
                "overall_risk_level": analysis.overall_risk_level.value,
                "gaps_identified": len(analysis.weak_alignments),
                "metrics_missing": len(analysis.missing_metrics),
            }
            for analysis in analyses
        ]

        logger.info(f"Generated risk timeline with {len(timeline)} data points for RFP {rfp_id}")

        return timeline
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating risk timeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate risk timeline",
        )
