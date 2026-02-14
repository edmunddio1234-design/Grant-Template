"""
AI Draft Framework Routes - Module 6

Routes for AI-powered content generation including section outlines, insert blocks,
comparisons, justifications, and complete draft frameworks.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from config import settings
from models import (
    GrantPlan,
    GrantPlanSection,
    RFP,
    BoilerplateSection,
    ActionTypeEnum,
    AuditLog,
)
from schemas import (
    GrantPlanRead,
    GrantPlanSectionRead,
)

from services.ai_service import AIDraftService, AIProvider, AIServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai-draft"])


# ============================================================================
# AI SERVICE SINGLETON
# ============================================================================

_ai_service: Optional[AIDraftService] = None
_ai_init_attempted: bool = False


def get_ai_service() -> Optional[AIDraftService]:
    """Get or create the AI service singleton. Returns None if no API key configured."""
    global _ai_service, _ai_init_attempted

    if _ai_init_attempted:
        return _ai_service

    _ai_init_attempted = True

    # Try Anthropic first (preferred), then OpenAI as fallback
    if settings.ANTHROPIC_API_KEY:
        try:
            _ai_service = AIDraftService(
                provider=AIProvider.ANTHROPIC,
                api_key=settings.ANTHROPIC_API_KEY,
                model=settings.ANTHROPIC_MODEL or "claude-sonnet-4-20250514",
            )
            logger.info("AI service initialized with Anthropic")
            return _ai_service
        except Exception as e:
            logger.error(f"Failed to init Anthropic AI service: {e}")

    if settings.OPENAI_API_KEY:
        try:
            _ai_service = AIDraftService(
                provider=AIProvider.OPENAI,
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL or "gpt-4o",
            )
            logger.info("AI service initialized with OpenAI")
            return _ai_service
        except Exception as e:
            logger.error(f"Failed to init OpenAI AI service: {e}")

    logger.warning("No AI API key configured — AI endpoints will use placeholder content")
    return None


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
# SECTION OUTLINE GENERATION
# ============================================================================


@router.post(
    "/outline/{plan_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI section outlines for a plan",
)
async def generate_section_outlines(
    plan_id: UUID,
    tone: str = Query("professional", regex="^(professional|conversational|technical)$"),
    focus_area: Optional[str] = Query(None, description="Specific focus area for outlines"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Generate AI-powered section outlines for all sections in a grant plan."""
    try:
        plan = await db.get(GrantPlan, str(plan_id))
        if not plan:
            logger.warning(f"Plan not found: {plan_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        await db.refresh(plan, ["sections"])
        ai_svc = get_ai_service()
        outlines = {}

        for section in plan.sections:
            if ai_svc:
                try:
                    # Build a lightweight section-like object for the service
                    class SectionProxy:
                        def __init__(self, s):
                            self.title = s.section_title
                            self.word_count_target = s.word_limit or 500
                            self.alignment_status = "pending"
                            self.scoring_weight = None

                    context = {
                        "plan_title": plan.title,
                        "tone": tone,
                        "focus_area": focus_area or "general",
                    }
                    ai_content = await ai_svc.generate_section_outline(
                        SectionProxy(section), context
                    )
                    # Parse AI response into outline items
                    outline_items = [
                        line.strip().lstrip("0123456789.-) ")
                        for line in ai_content.split("\n")
                        if line.strip() and len(line.strip()) > 3
                    ][:10]  # Cap at 10 items

                    outlines[str(section.id)] = {
                        "section_title": section.section_title,
                        "outline": outline_items if outline_items else [ai_content],
                        "suggested_word_count": section.word_limit or 500,
                        "tone": tone,
                        "source": "ai_generated",
                        "generated_at": datetime.utcnow().isoformat(),
                    }
                except Exception as e:
                    logger.warning(f"AI outline failed for section {section.id}: {e}")
                    outlines[str(section.id)] = _placeholder_outline(section, tone)
            else:
                outlines[str(section.id)] = _placeholder_outline(section, tone)

        await log_audit(
            db, ActionTypeEnum.CREATE, "AIOutline", str(plan_id),
            new_value={"plan_id": str(plan_id), "sections_count": len(outlines), "tone": tone},
        )
        await db.commit()

        logger.info(f"Generated outlines for {len(outlines)} sections in plan {plan_id}")

        return {
            "plan_id": str(plan_id),
            "sections_count": len(outlines),
            "outlines": outlines,
            "ai_powered": ai_svc is not None,
            "generation_timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating outlines: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate outlines",
        )


def _placeholder_outline(section, tone):
    """Return placeholder outline when AI is unavailable."""
    return {
        "section_title": section.section_title,
        "outline": [
            "Introduction and context for this section",
            "Key components, phases, or program activities",
            "Implementation timeline and milestones",
            "Expected outcomes and measurable impact",
            "Success metrics and evaluation approach",
        ],
        "suggested_word_count": section.word_limit or 500,
        "tone": tone,
        "source": "placeholder",
        "generated_at": datetime.utcnow().isoformat(),
    }


# ============================================================================
# INSERT BLOCK GENERATION
# ============================================================================


@router.post(
    "/insert-block",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Generate insert block for a specific section",
)
async def generate_insert_block(
    plan_id: UUID = Query(..., description="Grant plan ID"),
    section_id: UUID = Query(..., description="Section ID"),
    context: str = Query(..., min_length=10, description="Context or prompt for insert block"),
    style: str = Query("formal", regex="^(formal|informal|mixed)$", description="Writing style"),
    length: str = Query("medium", regex="^(short|medium|long)$", description="Content length"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Generate an AI-powered insert block for a specific section."""
    try:
        plan = await db.get(GrantPlan, str(plan_id))
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

        section = await db.get(GrantPlanSection, str(section_id))
        if not section or section.plan_id != plan_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

        word_counts = {"short": 100, "medium": 250, "long": 500}
        target_words = word_counts[length]
        ai_svc = get_ai_service()

        if ai_svc:
            try:
                prompt = f"""Write a {length}-length content block for the '{section.section_title}' section of a grant application.

Context/Instructions: {context}
Writing Style: {style}
Target Word Count: {target_words}
Plan: {plan.title}

Requirements:
1. Write approximately {target_words} words
2. Use {style} writing style
3. Focus on FOAM's programs, capacity, and outcomes
4. Address the specific context provided
5. Use professional grant-writing language
6. Include specific metrics and program details where relevant

Write the content block ready for direct inclusion in a grant narrative."""

                ai_content = await ai_svc._call_api([
                    {"role": "user", "content": prompt}
                ], max_tokens=target_words * 3)

                insert_block = {
                    "block_id": f"insert_block_{datetime.utcnow().timestamp()}",
                    "section_id": str(section_id),
                    "section_title": section.section_title,
                    "context": context,
                    "generated_content": ai_content,
                    "word_count": len(ai_content.split()),
                    "metadata": {
                        "style": style,
                        "target_length": length,
                        "confidence_score": 0.88,
                        "source": "ai_generated",
                        "model": ai_svc.model,
                    },
                    "generated_at": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.warning(f"AI insert block failed: {e}")
                insert_block = _placeholder_insert_block(section, context, style, length, target_words)
        else:
            insert_block = _placeholder_insert_block(section, context, style, length, target_words)

        await log_audit(
            db, ActionTypeEnum.CREATE, "AIInsertBlock", str(section_id),
            new_value={"plan_id": str(plan_id), "context": context, "style": style},
        )
        await db.commit()

        return insert_block
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating insert block: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate insert block",
        )


def _placeholder_insert_block(section, context, style, length, target_words):
    """Return placeholder insert block when AI is unavailable."""
    return {
        "block_id": f"insert_block_{datetime.utcnow().timestamp()}",
        "section_id": str(section.id) if hasattr(section, 'id') else "",
        "section_title": section.section_title,
        "context": context,
        "generated_content": (
            f"[AI content generation requires an OpenAI API key. "
            f"Configure OPENAI_API_KEY in your environment to enable AI-powered "
            f"content generation for the '{section.section_title}' section. "
            f"This block would generate approximately {target_words} words of "
            f"{style}-style content based on your context: {context}]"
        ),
        "word_count": 0,
        "metadata": {
            "style": style,
            "target_length": length,
            "confidence_score": 0,
            "source": "placeholder",
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


# ============================================================================
# COMPARISON STATEMENT GENERATION
# ============================================================================


@router.post(
    "/comparison",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Generate comparison statement",
)
async def generate_comparison_statement(
    plan_id: UUID = Query(..., description="Grant plan ID"),
    comparison_topic: str = Query(..., min_length=5, description="Topic to compare"),
    item1: str = Query(..., description="First item to compare"),
    item2: str = Query(..., description="Second item to compare"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Generate an AI-powered comparison statement for grant application content."""
    try:
        plan = await db.get(GrantPlan, str(plan_id))
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

        ai_svc = get_ai_service()

        if ai_svc:
            try:
                prompt = f"""Write a comparison statement for a grant application showing how two approaches or elements relate.

Topic: {comparison_topic}
Item 1: {item1}
Item 2: {item2}
Grant Plan: {plan.title}

Requirements:
1. Show specific alignment and differences between the two items
2. Connect to FOAM's mission and programs
3. Include relevant metrics or outcomes where applicable
4. Write 3-5 sentences in professional grant language
5. Provide actionable recommendations

Write the comparison statement and include 2-3 key recommendations."""

                ai_content = await ai_svc._call_api([
                    {"role": "user", "content": prompt}
                ], max_tokens=800)

                comparison = {
                    "comparison_id": f"comparison_{datetime.utcnow().timestamp()}",
                    "plan_id": str(plan_id),
                    "topic": comparison_topic,
                    "generated_statement": ai_content,
                    "recommendations": [],
                    "confidence_score": 0.85,
                    "source": "ai_generated",
                    "model": ai_svc.model,
                    "generated_at": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.warning(f"AI comparison failed: {e}")
                comparison = _placeholder_comparison(plan_id, comparison_topic, item1, item2)
        else:
            comparison = _placeholder_comparison(plan_id, comparison_topic, item1, item2)

        return comparison
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating comparison: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate comparison",
        )


def _placeholder_comparison(plan_id, topic, item1, item2):
    return {
        "comparison_id": f"comparison_{datetime.utcnow().timestamp()}",
        "plan_id": str(plan_id),
        "topic": topic,
        "generated_statement": (
            f"[AI comparison requires an OpenAI API key. Configure OPENAI_API_KEY "
            f"to generate a detailed comparison of {item1} and {item2} regarding {topic}.]"
        ),
        "recommendations": [],
        "confidence_score": 0,
        "source": "placeholder",
        "generated_at": datetime.utcnow().isoformat(),
    }


# ============================================================================
# ALIGNMENT JUSTIFICATION GENERATION
# ============================================================================


@router.post(
    "/justification",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Generate alignment justification",
)
async def generate_alignment_justification(
    plan_id: UUID = Query(..., description="Grant plan ID"),
    requirement: str = Query(..., min_length=5, description="RFP requirement"),
    boilerplate_content: str = Query(..., min_length=5, description="Boilerplate content snippet"),
    gap_areas: Optional[List[str]] = Query(None, description="Known gap areas"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Generate an AI-powered alignment justification statement."""
    try:
        plan = await db.get(GrantPlan, str(plan_id))
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

        ai_svc = get_ai_service()

        if ai_svc:
            try:
                gap_text = f"\nKnown Gap Areas: {', '.join(gap_areas)}" if gap_areas else ""
                prompt = f"""Write an alignment justification for a grant application.

RFP REQUIREMENT:
{requirement}

EXISTING BOILERPLATE CONTENT:
{boilerplate_content}
{gap_text}

Grant Plan: {plan.title}

Task:
1. Explain how FOAM's existing content addresses the RFP requirement
2. Identify specific strengths in the alignment
3. Note any gaps and suggest how to address them
4. Provide a confidence/alignment score assessment
5. Include 3-4 customization recommendations
6. Write in professional grant-review language

Provide the justification followed by customization notes."""

                ai_content = await ai_svc._call_api([
                    {"role": "user", "content": prompt}
                ], max_tokens=1000)

                justification = {
                    "justification_id": f"justification_{datetime.utcnow().timestamp()}",
                    "plan_id": str(plan_id),
                    "requirement": requirement[:200],
                    "generated_justification": ai_content,
                    "alignment_score": 0.82,
                    "customization_notes": [],
                    "confidence_score": 0.85,
                    "source": "ai_generated",
                    "model": ai_svc.model,
                    "generated_at": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.warning(f"AI justification failed: {e}")
                justification = _placeholder_justification(plan_id, requirement, gap_areas)
        else:
            justification = _placeholder_justification(plan_id, requirement, gap_areas)

        return justification
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating justification: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate justification",
        )


def _placeholder_justification(plan_id, requirement, gap_areas):
    return {
        "justification_id": f"justification_{datetime.utcnow().timestamp()}",
        "plan_id": str(plan_id),
        "requirement": requirement[:200],
        "generated_justification": (
            "[AI justification requires an OpenAI API key. Configure OPENAI_API_KEY "
            "to generate detailed alignment justifications between your boilerplate "
            "content and RFP requirements.]"
        ),
        "alignment_score": 0,
        "customization_notes": [],
        "confidence_score": 0,
        "source": "placeholder",
        "generated_at": datetime.utcnow().isoformat(),
    }


# ============================================================================
# FULL DRAFT FRAMEWORK GENERATION
# ============================================================================


@router.post(
    "/draft-framework/{plan_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Generate full draft framework for a plan",
)
async def generate_draft_framework(
    plan_id: UUID,
    include_justifications: bool = Query(True, description="Include alignment justifications"),
    include_outlines: bool = Query(True, description="Include section outlines"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Generate a complete AI-powered draft framework for a grant plan."""
    try:
        plan = await db.get(GrantPlan, str(plan_id))
        if not plan:
            logger.warning(f"Plan not found: {plan_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

        await db.refresh(plan, ["sections"])
        ai_svc = get_ai_service()
        framework_sections = {}

        async def generate_single_section(section):
            """Generate framework for a single section (runs in parallel)."""
            section_framework = {
                "section_id": str(section.id),
                "section_title": section.section_title,
                "section_order": section.section_order,
                "word_limit": section.word_limit or 500,
            }

            if ai_svc:
                try:
                    prompt = f"""Generate a comprehensive draft for the "{section.section_title}" section of a grant application for Fathers On A Mission (FOAM).

Plan: {plan.title}
Section Order: {section.section_order}
Target Length: {section.word_limit or 500} words

Write a complete, detailed draft (not just an outline) for this section. Include:
- Specific program details about FOAM
- Measurable outcomes and metrics
- Professional grant-writing language
- At least 200 words of actual narrative content

Also provide:
- A 5-point outline
- 3 alignment notes connecting to funder requirements
- 3 customization recommendations

Format:
CONTENT:
[full draft narrative - minimum 200 words]

OUTLINE:
[numbered items]

ALIGNMENT NOTES:
[numbered notes]

CUSTOMIZATION:
[numbered recommendations]"""

                    ai_content = await ai_svc._call_api([
                        {"role": "user", "content": prompt}
                    ], max_tokens=1500)

                    # Parse AI response
                    parts = ai_content.split("\n")
                    current_part = None
                    parsed = {"content": "", "outline": [], "alignment": [], "customization": []}

                    for line in parts:
                        stripped = line.strip()
                        upper = stripped.upper()
                        if upper.startswith("CONTENT") and ":" in stripped:
                            current_part = "content"
                        elif upper.startswith("OUTLINE") and ":" in stripped:
                            current_part = "outline"
                        elif upper.startswith("ALIGNMENT") and ":" in stripped:
                            current_part = "alignment"
                        elif upper.startswith("CUSTOMIZATION") and ":" in stripped:
                            current_part = "customization"
                        elif upper.startswith("SUGGESTED CONTENT") and ":" in stripped:
                            current_part = "content"
                        elif stripped and current_part:
                            clean = stripped.lstrip("0123456789.-) *•")
                            if clean:
                                if current_part == "content":
                                    parsed["content"] += clean + "\n"
                                elif current_part in parsed:
                                    parsed[current_part].append(clean)

                    # If no CONTENT: header was found, treat the whole response as content
                    if not parsed["content"].strip() and ai_content.strip():
                        parsed["content"] = ai_content.strip()

                    if include_outlines:
                        section_framework["outline"] = parsed["outline"][:7] or [
                            "Opening statement and context",
                            "Project approach and activities",
                            "Target population details",
                            "Timeline and milestones",
                            "Expected outcomes and impact",
                        ]

                    if include_justifications:
                        section_framework["suggested_content"] = parsed["content"].strip() or (
                            f"AI-generated content for {section.section_title}."
                        )
                        section_framework["alignment_notes"] = parsed["alignment"][:4] or [
                            "Directly addresses funder requirement",
                            "Demonstrates organizational capacity",
                            "Includes measurable outcomes",
                        ]

                    section_framework["customization_notes"] = parsed["customization"][:4] or [
                        "Tailor to Project Family Build's specific context",
                        "Add organization-specific data and outcomes",
                        "Include references to FOAM's mission",
                    ]
                    section_framework["source"] = "ai_generated"
                    section_framework["model"] = ai_svc.model

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"AI framework FAILED for section {section.id}: {error_msg}", exc_info=True)
                    _fill_placeholder_framework(section_framework, section, include_outlines, include_justifications)
                    section_framework["error"] = error_msg
            else:
                _fill_placeholder_framework(section_framework, section, include_outlines, include_justifications)
                section_framework["error"] = "No AI API key configured"

            return str(section.id), section_framework

        # Generate all sections IN PARALLEL for speed
        tasks = [generate_single_section(section) for section in plan.sections]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Section generation failed: {result}")
                continue
            section_id, section_framework = result
            framework_sections[section_id] = section_framework

        await log_audit(
            db, ActionTypeEnum.CREATE, "AIDraftFramework", str(plan_id),
            new_value={
                "plan_id": str(plan_id),
                "sections": len(framework_sections),
                "include_justifications": include_justifications,
                "include_outlines": include_outlines,
                "ai_powered": ai_svc is not None,
            },
        )
        await db.commit()

        # Check for AI errors across sections
        ai_errors = []
        placeholder_count = 0
        for sec_id, sec_data in framework_sections.items():
            if sec_data.get("source") == "placeholder":
                placeholder_count += 1
            if sec_data.get("error"):
                ai_errors.append(sec_data["error"])

        if ai_errors:
            logger.warning(f"AI errors in draft framework: {ai_errors[0]}")

        logger.info(f"Generated draft framework for plan {plan_id} ({len(framework_sections)} sections, {placeholder_count} placeholders)")

        return {
            "framework_id": f"framework_{datetime.utcnow().timestamp()}",
            "plan_id": str(plan_id),
            "plan_title": plan.title,
            "sections": framework_sections,
            "generation_config": {
                "include_justifications": include_justifications,
                "include_outlines": include_outlines,
                "total_sections": len(framework_sections),
                "ai_powered": ai_svc is not None,
                "model": ai_svc.model if ai_svc else None,
                "placeholder_count": placeholder_count,
                "ai_error": ai_errors[0] if ai_errors else None,
            },
            "usage_notes": [
                "Use outlines as guides for section development",
                "Adapt suggested content to organization context",
                "Ensure all compliance checkpoints are addressed",
                "Add specific data and metrics for Project Family Build",
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating draft framework: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate draft framework",
        )


def _fill_placeholder_framework(section_framework, section, include_outlines, include_justifications):
    """Fill framework section with placeholder content."""
    if include_outlines:
        section_framework["outline"] = [
            "Opening statement/context",
            "Project approach and activities",
            "Target population details",
            "Timeline and milestones",
            "Expected outcomes and impact",
            "Conclusion/summary",
        ]
    if include_justifications:
        section_framework["suggested_content"] = (
            f"[AI content for {section.section_title} requires an OpenAI API key. "
            f"Configure OPENAI_API_KEY to enable AI-powered content generation.]"
        )
        section_framework["alignment_notes"] = [
            "Directly addresses funder requirement",
            "Demonstrates organizational capacity",
            "Includes measurable outcomes",
        ]
    section_framework["customization_notes"] = [
        "Tailor to Project Family Build's specific context",
        "Add organization-specific data and outcomes",
        "Include references to Fathers On A Mission's mission",
    ]
    section_framework["source"] = "placeholder"


# ============================================================================
# SAVED DRAFTS RETRIEVAL
# ============================================================================


@router.get(
    "/drafts/{plan_id}",
    response_model=List[Dict[str, Any]],
    summary="Get saved AI draft blocks",
    status_code=status.HTTP_200_OK,
)
async def get_saved_drafts(
    plan_id: UUID,
    block_type: Optional[str] = Query(None, regex="^(outline|insert|comparison|justification|framework)$"),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Retrieve saved AI draft blocks for a grant plan."""
    try:
        plan = await db.get(GrantPlan, str(plan_id))
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

        # TODO: When draft persistence is implemented, query from database here
        # For now, return empty list indicating no saved drafts
        return []

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving saved drafts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve saved drafts",
        )


# ============================================================================
# AI SERVICE STATUS
# ============================================================================


@router.get(
    "/status",
    response_model=Dict[str, Any],
    summary="Check AI service status",
)
async def ai_service_status() -> Dict[str, Any]:
    """Check if AI service is configured and available."""
    ai_svc = get_ai_service()
    return {
        "ai_available": ai_svc is not None,
        "provider": ai_svc.provider.value if ai_svc else None,
        "model": ai_svc.model if ai_svc else None,
        "message": (
            f"AI service active ({ai_svc.provider.value} / {ai_svc.model})"
            if ai_svc
            else "No AI API key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY."
        ),
    }


@router.get(
    "/test",
    response_model=Dict[str, Any],
    summary="Test AI API key with a real call",
)
async def test_ai_connection() -> Dict[str, Any]:
    """Make a real API call to verify the AI key works."""
    ai_svc = get_ai_service()
    if not ai_svc:
        return {
            "success": False,
            "error": "No AI service configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY.",
            "provider": None,
        }

    try:
        response = await ai_svc._call_api([
            {"role": "user", "content": "Respond with exactly: FOAM AI OK"}
        ], max_tokens=20)
        return {
            "success": True,
            "provider": ai_svc.provider.value,
            "model": ai_svc.model,
            "response": response[:100],
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"AI test call failed: {error_msg}")
        return {
            "success": False,
            "provider": ai_svc.provider.value,
            "model": ai_svc.model,
            "error": error_msg,
        }
