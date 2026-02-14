"""
Plan Generator Service

Generates structured grant application plans from RFP analysis and crosswalk results.
Allocates word counts, suggests content blocks, and builds compliance checklists.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class ComplianceItem:
    """Single compliance requirement and status."""
    requirement: str
    status: str  # met/partial/unmet
    notes: str
    section: Optional[str] = None
    evidence: Optional[str] = None


@dataclass
class PlanSection:
    """Single section in the grant plan."""
    title: str
    order: int
    word_count_target: int
    suggested_content_blocks: List[str] = field(default_factory=list)
    customization_notes: List[str] = field(default_factory=list)
    compliance_items: List[ComplianceItem] = field(default_factory=list)
    scoring_weight: Optional[float] = None
    risk_level: str = "green"  # green/yellow/red
    alignment_status: str = "strong"  # strong/partial/weak/none
    boilerplate_reference: Optional[str] = None
    estimated_hours: int = 5


@dataclass
class GrantPlan:
    """Complete grant application plan."""
    title: str
    rfp_title: str
    funder_name: str
    total_sections: int
    overall_compliance_score: float  # 0-100
    sections: List[PlanSection] = field(default_factory=list)
    compliance_checklist: List[ComplianceItem] = field(default_factory=list)
    scoring_summary: Dict[str, Any] = field(default_factory=dict)
    customization_priority: List[str] = field(default_factory=list)
    estimated_total_words: int = 0
    estimated_total_hours: int = 0
    gap_analysis_summary: Optional[str] = None
    submission_timeline: Optional[str] = None


class PlanGeneratorService:
    """
    Service for generating structured grant application plans.

    Combines RFP analysis, crosswalk results, and gap analysis to produce
    actionable section-by-section plans with word count targets and content suggestions.
    """

    # Standard RFP section order and importance
    STANDARD_SECTIONS = [
        ("need_statement", "Need Statement / Problem Description", 0.15),
        ("organizational_capacity", "Organizational Capacity", 0.15),
        ("project_design", "Project Design / Program Description", 0.25),
        ("evaluation_plan", "Evaluation Plan", 0.15),
        ("budget", "Budget Narrative", 0.15),
        ("sustainability", "Sustainability Plan", 0.10),
        ("timeline", "Timeline / Work Plan", 0.05),
    ]

    def __init__(self):
        """Initialize the Plan Generator Service."""
        pass

    async def generate_plan(self, parsed_rfp, crosswalk_results: List,
                           gap_analysis) -> GrantPlan:
        """
        Generate comprehensive grant application plan.

        Args:
            parsed_rfp: ParsedRFP from parser
            crosswalk_results: List of CrosswalkResult from crosswalk engine
            gap_analysis: GapAnalysis from gap analyzer

        Returns:
            GrantPlan object
        """
        try:
            # Run plan generation tasks in parallel
            tasks = [
                asyncio.to_thread(self._create_sections, parsed_rfp, crosswalk_results),
                asyncio.to_thread(self._build_compliance_checklist, parsed_rfp, crosswalk_results),
                asyncio.to_thread(self._calculate_compliance_score, None),  # Will be set after checklist
                asyncio.to_thread(self._build_scoring_summary, parsed_rfp, crosswalk_results),
            ]

            section_results = await asyncio.gather(*tasks, return_exceptions=True)

            sections = section_results[0] if not isinstance(section_results[0], Exception) else []
            compliance_checklist = section_results[1] if not isinstance(section_results[1], Exception) else []
            scoring_summary = section_results[3] if not isinstance(section_results[3], Exception) else {}

            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(compliance_checklist)

            # Allocate word counts
            self._allocate_word_counts(sections, parsed_rfp)

            # Add content suggestions
            for section in sections:
                section.suggested_content_blocks = self._suggest_content(section, crosswalk_results)

            # Generate customization priority
            customization_priority = self._generate_customization_priority(
                sections, gap_analysis
            )

            # Estimate totals
            estimated_total_words = sum(s.word_count_target for s in sections)
            estimated_total_hours = sum(s.estimated_hours for s in sections)

            # Create plan
            plan = GrantPlan(
                title=f"Grant Application Plan: {parsed_rfp.title}",
                rfp_title=parsed_rfp.title,
                funder_name=parsed_rfp.funder_name,
                total_sections=len(sections),
                overall_compliance_score=compliance_score,
                sections=sections,
                compliance_checklist=compliance_checklist,
                scoring_summary=scoring_summary,
                customization_priority=customization_priority,
                estimated_total_words=estimated_total_words,
                estimated_total_hours=estimated_total_hours,
                gap_analysis_summary=self._summarize_gap_analysis(gap_analysis),
                submission_timeline=self._generate_timeline(estimated_total_hours)
            )

            logger.info(
                f"Generated plan: {plan.title} with {len(sections)} sections, "
                f"{estimated_total_words} target words, {compliance_score:.1f}% compliance"
            )

            return plan

        except Exception as e:
            logger.error(f"Error generating plan: {str(e)}", exc_info=True)
            raise

    def _create_sections(self, parsed_rfp, crosswalk_results: List) -> List[PlanSection]:
        """
        Create plan sections from RFP structure and crosswalk results.

        Args:
            parsed_rfp: ParsedRFP object
            crosswalk_results: List of CrosswalkResult objects

        Returns:
            List of PlanSection objects
        """
        sections = []
        order = 1

        # Map RFP sections to standard section types
        for section in parsed_rfp.sections:
            section_name = section.name.lower()

            # Find matching standard section
            matched_standard = None
            for std_key, std_title, std_weight in self.STANDARD_SECTIONS:
                if std_key in section_name or section_name in std_key:
                    matched_standard = (std_key, std_title, std_weight)
                    break

            if not matched_standard:
                # Use RFP section name as-is
                title = section.name
                weight = 0.1
            else:
                title = matched_standard[1]
                weight = matched_standard[2]

            # Find related crosswalk results
            related_results = [
                r for r in crosswalk_results
                if r.rfp_section.lower() == section_name
            ]

            # Determine alignment and risk
            if related_results:
                alignment = related_results[0].alignment_level.value
                risk = related_results[0].risk_level.value
            else:
                alignment = "unknown"
                risk = "yellow"

            # Get word limit from RFP
            word_limit = section.word_limit or 500

            plan_section = PlanSection(
                title=title,
                order=order,
                word_count_target=word_limit,
                scoring_weight=weight,
                risk_level=risk,
                alignment_status=alignment,
                boilerplate_reference=None,
                estimated_hours=self._estimate_hours(word_limit)
            )

            sections.append(plan_section)
            order += 1

        logger.debug(f"Created {len(sections)} plan sections")
        return sections

    def _allocate_word_counts(self, sections: List[PlanSection], parsed_rfp) -> None:
        """
        Allocate word counts to sections based on RFP limits and scoring weights.

        Args:
            sections: List of PlanSection objects to modify in place
            parsed_rfp: ParsedRFP object
        """
        # Get total available words
        total_words = sum(s.word_limit or 500 for s in parsed_rfp.sections)

        for section in sections:
            # Find corresponding RFP section
            rfp_section = next(
                (s for s in parsed_rfp.sections if s.name.lower() in section.title.lower()),
                None
            )

            if rfp_section and rfp_section.word_limit:
                section.word_count_target = rfp_section.word_limit
            else:
                # Allocate based on scoring weight
                if section.scoring_weight:
                    section.word_count_target = int(total_words * section.scoring_weight)
                else:
                    section.word_count_target = int(total_words / len(sections))

            # Add 20% buffer for formatting flexibility
            section.word_count_target = int(section.word_count_target * 1.0)

        logger.debug(f"Allocated word counts for {len(sections)} sections")

    def _suggest_content(self, section: PlanSection, crosswalk_results: List) -> List[str]:
        """
        Suggest content blocks for a section.

        Args:
            section: PlanSection object
            crosswalk_results: List of CrosswalkResult objects

        Returns:
            List of suggested content block descriptions
        """
        suggestions = []

        # Find related crosswalk results
        related = [
            r for r in crosswalk_results
            if r.rfp_section.lower() in section.title.lower()
        ]

        if not related:
            if section.alignment_status == "strong":
                suggestions.append(f"Use boilerplate for {section.title} (strong alignment)")
            elif section.alignment_status == "partial":
                suggestions.append(f"Adapt boilerplate for {section.title}; add RFP-specific details")
            else:
                suggestions.append(f"Develop custom content for {section.title}")
            return suggestions

        # Add suggestions based on crosswalk results
        for result in related[:3]:
            if result.alignment_level.value == "strong":
                suggestions.append(
                    f"Use boilerplate from {result.boilerplate_section}: "
                    f"{result.boilerplate_excerpt[:80]}..."
                )
            elif result.alignment_level.value == "partial":
                suggestions.append(
                    f"Adapt boilerplate from {result.boilerplate_section}; "
                    f"supplement with: {result.customization_needed}"
                )
            else:
                suggestions.append(
                    f"Develop custom narrative emphasizing: {result.recommended_actions[0] if result.recommended_actions else 'RFP alignment'}"
                )

        # Add section-specific suggestions
        if "need" in section.title.lower():
            suggestions.append("Open with organizational target population context (140 fathers, ~210 children)")
            suggestions.append("Reference East Baton Rouge Parish demographics and needs data")

        elif "organizational" in section.title.lower():
            suggestions.append("Lead with 501(c)(3) status and nonprofit history")
            suggestions.append("Highlight relevant program experience and outcomes")
            suggestions.append("Include staff qualifications and organizational structure")

        elif "design" in section.title.lower():
            suggestions.append("Describe three-part organizational model: Project Family Build, Responsible Fatherhood Classes, Celebration events")
            suggestions.append("Include evidence-based practice references (NPCL curriculum, wraparound model)")
            suggestions.append("Detail target population and service delivery approach")

        elif "evaluation" in section.title.lower():
            suggestions.append("Present logic model connecting activities to outcomes")
            suggestions.append("Define specific, measurable outcomes (80%/75%/70% targets)")
            suggestions.append("Describe EmpowerDB/nFORM data collection and reporting")

        elif "budget" in section.title.lower():
            suggestions.append("Connect all line items to program design and outcomes")
            suggestions.append("Justify staffing, training, and capacity building costs")
            suggestions.append("Show cost-effectiveness analysis if RFP requires")

        elif "sustainability" in section.title.lower():
            suggestions.append("Detail diversified funding strategy beyond grant period")
            suggestions.append("Show evidence of community investment and partnerships")
            suggestions.append("Connect to organizational strategic plan")

        logger.debug(f"Generated {len(suggestions)} content suggestions for {section.title}")
        return suggestions

    def _build_compliance_checklist(self, parsed_rfp, crosswalk_results: List) -> List[ComplianceItem]:
        """
        Build compliance checklist from RFP requirements.

        Args:
            parsed_rfp: ParsedRFP object
            crosswalk_results: List of CrosswalkResult objects

        Returns:
            List of ComplianceItem objects
        """
        checklist = []

        # Check sections present
        for section in parsed_rfp.sections:
            status = "met"
            notes = f"Section: {section.name}"

            # Check if this section has strong alignment
            related = [
                r for r in crosswalk_results
                if r.rfp_section.lower() == section.name.lower()
            ]

            if related:
                result = related[0]
                if result.alignment_level.value == "strong":
                    notes += " - Strong organizational alignment"
                elif result.alignment_level.value == "partial":
                    status = "partial"
                    notes += " - Partial organizational alignment; requires customization"
                else:
                    status = "unmet"
                    notes += " - No organizational alignment; custom content needed"

            checklist.append(ComplianceItem(
                requirement=f"Complete {section.name}",
                status=status,
                notes=notes,
                section=section.name
            ))

        # Check formatting requirements
        for fmt_req in parsed_rfp.formatting_requirements[:5]:
            checklist.append(ComplianceItem(
                requirement=f"Formatting: {fmt_req}",
                status="pending",
                notes="Must verify before final submission"
            ))

        # Check eligibility requirements
        for elig in parsed_rfp.eligibility[:3]:
            checklist.append(ComplianceItem(
                requirement=f"Eligibility: {elig}",
                status="met",
                notes="The organization meets this requirement"
            ))

        # Check required attachments
        for attachment in parsed_rfp.required_attachments[:5]:
            checklist.append(ComplianceItem(
                requirement=f"Attachment: {attachment}",
                status="pending",
                notes="Must prepare before submission"
            ))

        # Check scoring criteria coverage
        for criterion in parsed_rfp.scoring_criteria[:5]:
            checklist.append(ComplianceItem(
                requirement=f"Scoring: {criterion.description}",
                status="pending",
                notes=f"Worth {criterion.max_points} points"
            ))

        logger.debug(f"Built compliance checklist with {len(checklist)} items")
        return checklist

    def _calculate_compliance_score(self, compliance_checklist: List[ComplianceItem]) -> float:
        """
        Calculate overall compliance score.

        Args:
            compliance_checklist: List of ComplianceItem objects

        Returns:
            Compliance score (0-100)
        """
        if not compliance_checklist:
            return 0.0

        met = sum(1 for item in compliance_checklist if item.status == "met")
        partial = sum(1 for item in compliance_checklist if item.status == "partial")
        unmet = sum(1 for item in compliance_checklist if item.status == "unmet")
        pending = sum(1 for item in compliance_checklist if item.status == "pending")

        # Calculate score: met=100%, partial=50%, unmet/pending=0%
        points = (met * 100) + (partial * 50)
        total_points = len(compliance_checklist) * 100

        score = (points / total_points * 100) if total_points > 0 else 0.0
        return min(100.0, max(0.0, score))

    def _build_scoring_summary(self, parsed_rfp, crosswalk_results: List) -> Dict[str, Any]:
        """
        Build summary of RFP scoring criteria and alignment.

        Args:
            parsed_rfp: ParsedRFP object
            crosswalk_results: List of CrosswalkResult objects

        Returns:
            Dictionary with scoring summary
        """
        summary = {
            "total_points_available": 0,
            "criteria_by_section": {},
            "alignment_by_criteria": [],
            "scoring_recommendations": []
        }

        for criterion in parsed_rfp.scoring_criteria:
            summary["total_points_available"] += criterion.max_points

            if criterion.section not in summary["criteria_by_section"]:
                summary["criteria_by_section"][criterion.section] = []

            summary["criteria_by_section"][criterion.section].append({
                "description": criterion.description,
                "points": criterion.max_points,
                "weight": criterion.weight
            })

        # Map scoring criteria to crosswalk results
        for criterion in parsed_rfp.scoring_criteria[:5]:
            related = [
                r for r in crosswalk_results
                if criterion.section.lower() in r.rfp_section.lower()
            ]

            if related:
                best_match = max(related, key=lambda r: r.alignment_score)
                summary["alignment_by_criteria"].append({
                    "criterion": criterion.description,
                    "alignment": best_match.alignment_level.value,
                    "score": best_match.alignment_score
                })

        # Generate scoring recommendations
        for section, criteria in summary["criteria_by_section"].items():
            total_section_points = sum(c["points"] for c in criteria)
            summary["scoring_recommendations"].append(
                f"Allocate {sum(s['word_count_target'] for s in [] if True)//len([]) or 500} "
                f"words to {section} (worth {total_section_points} points)"
            )

        return summary

    def _generate_customization_priority(self, sections: List[PlanSection],
                                        gap_analysis) -> List[str]:
        """
        Generate prioritized customization list.

        Args:
            sections: List of PlanSection objects
            gap_analysis: GapAnalysis object

        Returns:
            Ordered list of customization priorities
        """
        priorities = []

        # High-weight sections with weak alignment
        weak_high_weight = [
            s for s in sections
            if s.scoring_weight and s.scoring_weight > 0.15
            and s.alignment_status in ["weak", "partial"]
        ]

        for section in sorted(weak_high_weight, key=lambda s: s.scoring_weight or 0, reverse=True):
            priorities.append(
                f"1. Strengthen {section.title} ({section.scoring_weight*100:.0f}% weight, "
                f"{section.alignment_status} alignment)"
            )

        # Red-risk sections
        red_sections = [s for s in sections if s.risk_level == "red"]
        for section in red_sections:
            priorities.append(f"2. Resolve red-risk {section.title}")

        # Gap analysis recommendations
        if gap_analysis and gap_analysis.top_recommendations:
            for i, rec in enumerate(gap_analysis.top_recommendations[:3], start=3):
                priorities.append(f"{i}. {rec}")

        return priorities

    def _estimate_hours(self, word_count: int) -> int:
        """
        Estimate hours needed to write a section.

        Args:
            word_count: Target word count

        Returns:
            Estimated hours
        """
        # Estimate: 200 words per hour for grant writing
        base_hours = word_count / 200
        # Add 50% buffer for research, revision, coordination
        return int(base_hours * 1.5) or 1

    def _summarize_gap_analysis(self, gap_analysis) -> str:
        """
        Summarize gap analysis findings.

        Args:
            gap_analysis: GapAnalysis object

        Returns:
            Summary string
        """
        if not gap_analysis:
            return "No gap analysis available"

        summary = (
            f"Overall Risk: {gap_analysis.overall_risk_level.upper()} "
            f"(Score: {gap_analysis.overall_score:.0f}/100). "
            f"Key gaps: {gap_analysis.risk_distribution.get('red', 0)} red-level, "
            f"{gap_analysis.risk_distribution.get('yellow', 0)} yellow-level findings."
        )

        if gap_analysis.top_recommendations:
            summary += f" Top priority: {gap_analysis.top_recommendations[0]}"

        return summary

    def _generate_timeline(self, estimated_hours: int) -> str:
        """
        Generate recommended submission timeline.

        Args:
            estimated_hours: Total estimated hours

        Returns:
            Timeline recommendation
        """
        weeks_needed = max(1, estimated_hours // 10)  # Assume 10 hours/week

        if weeks_needed <= 2:
            return "2 weeks (expedited timeline; prioritize customization)"
        elif weeks_needed <= 4:
            return "4 weeks (standard timeline)"
        elif weeks_needed <= 8:
            return "8 weeks (comprehensive development and multiple review cycles)"
        else:
            return f"{weeks_needed} weeks (complex application; consider team division of labor)"
