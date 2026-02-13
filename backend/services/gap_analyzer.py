"""
Gap Analyzer Service

Analyzes crosswalk results to produce comprehensive gap analysis including
severity categorization, risk assessment, and prioritized recommendations.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class GapSeverity(str, Enum):
    """Enumeration of gap severities."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass
class GapFinding:
    """A single gap finding with description and recommendations."""
    category: str  # metrics, alignment, data, partnerships, match, evaluation
    description: str
    severity: GapSeverity
    recommendation: str
    priority: int  # 1 (highest) to 5 (lowest)
    affected_section: Optional[str] = None
    evidence: Optional[str] = None


@dataclass
class GapAnalysis:
    """Complete gap analysis results."""
    overall_risk_level: str  # green/yellow/red
    overall_score: float  # 0-100
    findings: List[GapFinding] = field(default_factory=list)
    risk_distribution: Dict[str, int] = field(default_factory=dict)  # {green: X, yellow: Y, red: Z}
    category_scores: Dict[str, float] = field(default_factory=dict)  # category -> score (0-1)
    top_recommendations: List[str] = field(default_factory=list)
    missing_metrics: List[str] = field(default_factory=list)
    weak_alignments: List[str] = field(default_factory=list)
    outdated_data: List[str] = field(default_factory=list)
    missing_partnerships: List[str] = field(default_factory=list)
    match_gaps: List[str] = field(default_factory=list)
    evaluation_weaknesses: List[str] = field(default_factory=list)


class GapAnalyzerService:
    """
    Service for analyzing RFP-to-FOAM alignment gaps and generating insights.

    Categorizes gaps by type, calculates severity/risk, and generates
    prioritized recommendations for addressing weaknesses.
    """

    # Metric keywords that should appear in RFP/evaluation
    EXPECTED_METRICS = [
        "outcome", "measure", "metric", "target", "baseline", "evaluation",
        "assessment", "data collection", "performance", "indicator", "KPI"
    ]

    # Partnership keywords
    PARTNERSHIP_KEYWORDS = [
        "partner", "collaboration", "network", "referral", "coordination",
        "stakeholder", "community", "agency", "provider"
    ]

    # Evaluation framework keywords
    EVALUATION_KEYWORDS = [
        "evaluation", "assessment", "measurement", "outcomes", "logic model",
        "theory of change", "pre/post", "comparison", "data quality"
    ]

    def __init__(self):
        """Initialize the Gap Analyzer Service."""
        pass

    async def analyze(self, crosswalk_results: List, parsed_rfp) -> GapAnalysis:
        """
        Analyze crosswalk results and generate comprehensive gap analysis.

        Args:
            crosswalk_results: List of CrosswalkResult objects from crosswalk engine
            parsed_rfp: ParsedRFP object from parser

        Returns:
            GapAnalysis object with findings and recommendations
        """
        try:
            # Run all analysis tasks in parallel
            tasks = [
                asyncio.to_thread(self._categorize_gaps, crosswalk_results),
                asyncio.to_thread(self._check_metrics, parsed_rfp, crosswalk_results),
                asyncio.to_thread(self._check_partnerships, parsed_rfp),
                asyncio.to_thread(self._check_evaluation, parsed_rfp),
                asyncio.to_thread(self._identify_weak_alignments, crosswalk_results),
                asyncio.to_thread(self._check_outdated_data, parsed_rfp),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            gap_categories = results[0] if not isinstance(results[0], Exception) else {}
            missing_metrics = results[1] if not isinstance(results[1], Exception) else []
            missing_partnerships = results[2] if not isinstance(results[2], Exception) else []
            evaluation_weaknesses = results[3] if not isinstance(results[3], Exception) else []
            weak_alignments = results[4] if not isinstance(results[4], Exception) else []
            outdated_data = results[5] if not isinstance(results[5], Exception) else []

            # Build findings list
            findings = self._build_findings(
                gap_categories,
                missing_metrics,
                missing_partnerships,
                evaluation_weaknesses,
                weak_alignments,
                outdated_data
            )

            # Calculate scores
            overall_risk, overall_score = self._calculate_overall_risk(findings)
            risk_distribution = self._calculate_risk_distribution(findings)
            category_scores = self._calculate_category_scores(gap_categories, findings)

            # Generate recommendations
            top_recommendations = self._generate_top_recommendations(findings)

            gap_analysis = GapAnalysis(
                overall_risk_level=overall_risk,
                overall_score=overall_score,
                findings=findings,
                risk_distribution=risk_distribution,
                category_scores=category_scores,
                top_recommendations=top_recommendations,
                missing_metrics=missing_metrics,
                weak_alignments=weak_alignments,
                outdated_data=outdated_data,
                missing_partnerships=missing_partnerships,
                match_gaps=[item["gap"] for item in gap_categories.get("match", [])],
                evaluation_weaknesses=evaluation_weaknesses
            )

            logger.info(
                f"Gap analysis complete: {overall_risk} risk, {overall_score:.1f}/100 score, "
                f"{len(findings)} findings"
            )

            return gap_analysis

        except Exception as e:
            logger.error(f"Error during gap analysis: {str(e)}", exc_info=True)
            raise

    def _categorize_gaps(self, crosswalk_results: List) -> Dict:
        """
        Categorize gaps by type from crosswalk results.

        Args:
            crosswalk_results: List of CrosswalkResult objects

        Returns:
            Dictionary categorizing gaps
        """
        gaps = {
            "alignment": [],
            "match": []
        }

        for result in crosswalk_results:
            if result.gap_flag:
                gaps["alignment"].append({
                    "section": result.rfp_section,
                    "requirement": result.rfp_requirement,
                    "gap": f"No alignment found for {result.rfp_section}"
                })

            if result.alignment_level.value == "none":
                gaps["match"].append({
                    "section": result.rfp_section,
                    "foam_area": result.foam_strength,
                    "gap": f"No FOAM capability match for {result.rfp_section}"
                })

        logger.debug(f"Categorized gaps: {len(gaps['alignment'])} alignment, {len(gaps['match'])} match gaps")
        return gaps

    def _check_metrics(self, parsed_rfp, crosswalk_results: List) -> List[str]:
        """
        Check for missing or weak metrics in RFP.

        Args:
            parsed_rfp: ParsedRFP object
            crosswalk_results: List of CrosswalkResult objects

        Returns:
            List of missing metrics
        """
        missing_metrics = []

        # Combine all RFP content
        all_content = "\n".join([
            section.content for section in parsed_rfp.sections
        ])

        all_content_lower = all_content.lower()

        # Check for common metrics
        common_metrics = [
            "participant engagement rate",
            "completion rate",
            "program retention",
            "outcome achievement",
            "employment rate",
            "earnings increase",
            "recidivism reduction",
            "child welfare incidents",
            "parent-child interaction",
            "cost per participant"
        ]

        for metric in common_metrics:
            if metric not in all_content_lower:
                missing_metrics.append(metric)

        # Check evaluation section specifically
        for section in parsed_rfp.sections:
            if "evaluation" in section.name.lower():
                # Count metric keywords
                metric_count = sum(
                    1 for keyword in self.EXPECTED_METRICS
                    if keyword.lower() in section.content.lower()
                )

                if metric_count < 3:
                    missing_metrics.append(f"Weak evaluation metrics in {section.name}")

        logger.debug(f"Identified {len(missing_metrics)} missing/weak metrics")
        return missing_metrics[:10]

    def _check_partnerships(self, parsed_rfp) -> List[str]:
        """
        Check for missing partnership/collaboration requirements.

        Args:
            parsed_rfp: ParsedRFP object

        Returns:
            List of missing partnerships/collaboration gaps
        """
        missing_partnerships = []

        all_content = "\n".join([
            section.content for section in parsed_rfp.sections
        ])

        all_content_lower = all_content.lower()

        # Check for partnership/collaboration language
        partnership_count = sum(
            1 for keyword in self.PARTNERSHIP_KEYWORDS
            if keyword.lower() in all_content_lower
        )

        if partnership_count < 3:
            missing_partnerships.append("Limited collaboration/partnership requirements specified")

        # Check for specific partner types
        partner_types = [
            "child welfare agency",
            "workforce development",
            "education provider",
            "health provider",
            "community organizations"
        ]

        for partner_type in partner_types:
            if partner_type not in all_content_lower:
                missing_partnerships.append(f"No mention of {partner_type} partnership")

        logger.debug(f"Identified {len(missing_partnerships)} partnership gaps")
        return missing_partnerships[:8]

    def _check_evaluation(self, parsed_rfp) -> List[str]:
        """
        Check for evaluation framework weaknesses.

        Args:
            parsed_rfp: ParsedRFP object

        Returns:
            List of evaluation weaknesses
        """
        weaknesses = []

        evaluation_section = None
        for section in parsed_rfp.sections:
            if "evaluation" in section.name.lower():
                evaluation_section = section.content.lower()
                break

        if not evaluation_section:
            weaknesses.append("No dedicated evaluation plan section")
            return weaknesses

        # Check for key evaluation elements
        required_elements = [
            ("logic model", "Logic model or theory of change"),
            ("pre/post", "Pre-post assessment or comparison group"),
            ("data quality", "Data quality assurance procedures"),
            ("timeline", "Evaluation timeline and milestones"),
            ("responsible party", "Evaluation responsibility assigned"),
            ("outcome", "Specific outcome metrics defined")
        ]

        for keyword, description in required_elements:
            if keyword not in evaluation_section:
                weaknesses.append(f"Missing: {description}")

        logger.debug(f"Identified {len(weaknesses)} evaluation weaknesses")
        return weaknesses[:7]

    def _identify_weak_alignments(self, crosswalk_results: List) -> List[str]:
        """
        Identify sections with weak alignment to FOAM capabilities.

        Args:
            crosswalk_results: List of CrosswalkResult objects

        Returns:
            List of weak alignment descriptions
        """
        weak_alignments = []

        for result in crosswalk_results:
            if result.alignment_level.value in ["partial", "weak"]:
                weak_alignments.append(
                    f"{result.rfp_section}: {result.alignment_level.value} alignment "
                    f"(score: {result.alignment_score:.2f})"
                )

        logger.debug(f"Identified {len(weak_alignments)} weak alignments")
        return weak_alignments[:10]

    def _check_outdated_data(self, parsed_rfp) -> List[str]:
        """
        Check for outdated data references or timeframes.

        Args:
            parsed_rfp: ParsedRFP object

        Returns:
            List of outdated data issues
        """
        outdated = []

        all_content = "\n".join([
            section.content for section in parsed_rfp.sections
        ])

        # Look for old year references (before 2020)
        import re
        old_years = re.findall(r'\b(20[01][0-9])\b', all_content)
        if old_years:
            oldest_year = min(old_years)
            if int(oldest_year) < 2020:
                outdated.append(f"Data references from {oldest_year} may be outdated")

        # Check for "recent" or "current" without actual dates
        if "recent" in all_content.lower() and "202" not in all_content:
            outdated.append("Vague temporal references without specific dates")

        logger.debug(f"Identified {len(outdated)} outdated data issues")
        return outdated

    def _build_findings(self, gap_categories: Dict, missing_metrics: List,
                       missing_partnerships: List, evaluation_weaknesses: List,
                       weak_alignments: List, outdated_data: List) -> List[GapFinding]:
        """
        Build comprehensive list of GapFinding objects.

        Args:
            gap_categories: Categorized gaps
            missing_metrics: Missing metrics
            missing_partnerships: Partnership gaps
            evaluation_weaknesses: Evaluation weaknesses
            weak_alignments: Weak alignments
            outdated_data: Outdated data issues

        Returns:
            List of GapFinding objects
        """
        findings = []
        priority = 1

        # Alignment gaps (highest priority)
        for gap in gap_categories.get("alignment", []):
            findings.append(GapFinding(
                category="alignment",
                description=gap["gap"],
                severity=GapSeverity.RED,
                recommendation="Develop custom content for this section or reconsider FOAM program fit",
                priority=priority,
                affected_section=gap["section"]
            ))
            priority += 1

        # Match gaps
        for gap in gap_categories.get("match", []):
            findings.append(GapFinding(
                category="match",
                description=gap["gap"],
                severity=GapSeverity.YELLOW,
                recommendation=f"Explore connections to {gap['foam_area']} or identify new capability areas",
                priority=priority,
                affected_section=gap["section"]
            ))
            priority += 1

        # Missing metrics
        for metric in missing_metrics[:3]:
            findings.append(GapFinding(
                category="metrics",
                description=f"Missing metric or measurement approach: {metric}",
                severity=GapSeverity.YELLOW,
                recommendation="Develop measurement plan for this metric; coordinate with evaluation",
                priority=priority
            ))
            priority += 1

        # Missing partnerships
        for partnership in missing_partnerships[:3]:
            findings.append(GapFinding(
                category="partnerships",
                description=f"Partnership gap: {partnership}",
                severity=GapSeverity.YELLOW,
                recommendation="Establish partnerships or MOU before application submission",
                priority=priority
            ))
            priority += 1

        # Evaluation weaknesses
        for weakness in evaluation_weaknesses[:3]:
            findings.append(GapFinding(
                category="evaluation",
                description=f"Evaluation framework weakness: {weakness}",
                severity=GapSeverity.YELLOW,
                recommendation="Develop robust evaluation plan addressing all required components",
                priority=priority,
                affected_section="Evaluation Plan"
            ))
            priority += 1

        # Weak alignments
        for alignment in weak_alignments[:3]:
            findings.append(GapFinding(
                category="alignment",
                description=f"Weak alignment: {alignment}",
                severity=GapSeverity.YELLOW,
                recommendation="Strengthen alignment through targeted customization",
                priority=priority
            ))
            priority += 1

        # Outdated data
        for data_issue in outdated_data:
            findings.append(GapFinding(
                category="data",
                description=f"Data quality issue: {data_issue}",
                severity=GapSeverity.YELLOW,
                recommendation="Update data with current sources and timeframes",
                priority=priority
            ))
            priority += 1

        logger.debug(f"Built {len(findings)} findings")
        return findings

    def _calculate_overall_risk(self, findings: List[GapFinding]) -> tuple:
        """
        Calculate overall risk level and score from findings.

        Args:
            findings: List of GapFinding objects

        Returns:
            Tuple of (risk_level, score)
        """
        if not findings:
            return "green", 100.0

        # Count severities
        red_count = sum(1 for f in findings if f.severity == GapSeverity.RED)
        yellow_count = sum(1 for f in findings if f.severity == GapSeverity.YELLOW)
        green_count = sum(1 for f in findings if f.severity == GapSeverity.GREEN)

        # Determine overall risk
        if red_count >= 3:
            overall_risk = "red"
        elif red_count >= 1 or yellow_count >= 5:
            overall_risk = "yellow"
        else:
            overall_risk = "green"

        # Calculate score (0-100)
        # Start with 100, deduct for each finding
        score = 100.0
        score -= (red_count * 15)    # Red findings = 15 points each
        score -= (yellow_count * 5)   # Yellow findings = 5 points each
        score -= (green_count * 1)    # Green findings = 1 point each

        score = max(0.0, min(100.0, score))

        return overall_risk, score

    def _calculate_risk_distribution(self, findings: List[GapFinding]) -> Dict[str, int]:
        """
        Calculate distribution of risk levels.

        Args:
            findings: List of GapFinding objects

        Returns:
            Dictionary with counts by risk level
        """
        return {
            "green": sum(1 for f in findings if f.severity == GapSeverity.GREEN),
            "yellow": sum(1 for f in findings if f.severity == GapSeverity.YELLOW),
            "red": sum(1 for f in findings if f.severity == GapSeverity.RED)
        }

    def _calculate_category_scores(self, gap_categories: Dict, findings: List[GapFinding]) -> Dict[str, float]:
        """
        Calculate scores by gap category.

        Args:
            gap_categories: Categorized gaps
            findings: List of GapFinding objects

        Returns:
            Dictionary mapping category to score (0-1)
        """
        category_scores = {
            "alignment": 1.0,
            "match": 1.0,
            "metrics": 1.0,
            "partnerships": 1.0,
            "evaluation": 1.0,
            "data": 1.0
        }

        for finding in findings:
            if finding.category in category_scores:
                if finding.severity == GapSeverity.RED:
                    category_scores[finding.category] -= 0.3
                elif finding.severity == GapSeverity.YELLOW:
                    category_scores[finding.category] -= 0.15
                elif finding.severity == GapSeverity.GREEN:
                    category_scores[finding.category] -= 0.05

        # Clamp to 0-1
        return {k: max(0.0, min(1.0, v)) for k, v in category_scores.items()}

    def _generate_top_recommendations(self, findings: List[GapFinding]) -> List[str]:
        """
        Generate prioritized top recommendations.

        Args:
            findings: List of GapFinding objects

        Returns:
            List of top recommendations
        """
        # Sort by priority and severity
        sorted_findings = sorted(
            findings,
            key=lambda f: (f.priority, f.severity.value)
        )

        # Return top 5 recommendations
        recommendations = []
        for finding in sorted_findings[:5]:
            if finding.recommendation not in recommendations:
                recommendations.append(finding.recommendation)

        # Add summary recommendations
        red_findings = [f for f in findings if f.severity == GapSeverity.RED]
        if red_findings:
            recommendations.insert(0, "CRITICAL: Address red-level gaps before submission")

        yellow_findings = [f for f in findings if f.severity == GapSeverity.YELLOW]
        if len(yellow_findings) > 3:
            recommendations.insert(1, "HIGH PRIORITY: Significant strengthening needed in multiple areas")

        return recommendations[:8]
