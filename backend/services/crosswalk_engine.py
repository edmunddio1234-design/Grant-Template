"""
Crosswalk Engine Service

Core alignment engine that maps RFP requirements against FOAM boilerplate content.
Generates alignment scores, identifies gaps, and assigns risk levels.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import asyncio
import re

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    TfidfVectorizer = None
    cosine_similarity = None


logger = logging.getLogger(__name__)


class AlignmentLevel(str, Enum):
    """Enumeration of alignment levels."""
    STRONG = "strong"
    PARTIAL = "partial"
    WEAK = "weak"
    NONE = "none"


class RiskLevel(str, Enum):
    """Enumeration of risk levels."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


# FOAM-specific keyword mappings
FOAM_KEYWORD_MAP = {
    "reentry": [
        "Louisiana Barracks", "justice-involved", "recidivism", "DPS&C", "incarcerated",
        "reentry", "criminal justice", "formerly incarcerated", "post-incarceration"
    ],
    "fatherhood": [
        "Responsible Fatherhood Classes", "NPCL", "co-parenting", "father engagement",
        "paternity", "father presence", "fatherhood education", "parenting skills"
    ],
    "workforce": [
        "job readiness", "resume", "NCCER", "OSHA", "employment", "economic mobility",
        "career pathway", "job training", "vocational", "employment services"
    ],
    "case_management": [
        "Project Family Build", "Plans of Care", "wraparound", "barrier removal",
        "case management", "individualized", "service coordination", "continuity of care"
    ],
    "prevention": [
        "protective factors", "child welfare", "abuse prevention", "neglect",
        "prevention services", "family preservation", "family support"
    ],
    "evaluation": [
        "EmpowerDB", "nFORM", "pre/post assessment", "outcomes", "outcome measurement",
        "data collection", "metrics", "evaluation tool"
    ],
    "financial_literacy": [
        "budgeting", "banking", "credit", "financial empowerment", "financial management",
        "money management", "financial planning", "financial stability"
    ],
    "celebration_events": [
        "Celebration of Fatherhood", "events", "bonding", "engagement", "community",
        "celebration", "quarterly", "fatherhood event"
    ]
}


@dataclass
class CrosswalkResult:
    """Result of a single RFP requirement to FOAM capability alignment."""
    rfp_requirement: str
    rfp_section: str
    foam_strength: str  # FOAM capability area
    boilerplate_section: str
    boilerplate_excerpt: str
    alignment_score: float  # 0-1
    alignment_level: AlignmentLevel
    gap_flag: bool
    risk_level: RiskLevel
    customization_needed: str
    recommended_actions: List[str] = field(default_factory=list)
    confidence: float = 1.0


class CrosswalkEngine:
    """
    Core alignment engine for mapping RFP requirements to FOAM capabilities.

    Uses TF-IDF similarity, keyword matching, and program-specific logic to
    generate alignment scores and identify gaps.
    """

    def __init__(self, boilerplate_data: Optional[Dict] = None, use_ml: bool = True):
        """
        Initialize the Crosswalk Engine.

        Args:
            boilerplate_data: Dictionary of boilerplate sections keyed by area
            use_ml: Whether to use scikit-learn for similarity scoring
        """
        self.boilerplate_data = boilerplate_data or self._default_boilerplate()
        self.use_ml = use_ml and TfidfVectorizer is not None
        self.vectorizer = None

        if self.use_ml and TfidfVectorizer is not None:
            self._initialize_vectorizer()

        if not self.use_ml and TfidfVectorizer is None:
            logger.warning("scikit-learn not available; using keyword-based matching only")

    def _initialize_vectorizer(self) -> None:
        """Initialize TF-IDF vectorizer with boilerplate content."""
        if not self.use_ml:
            return

        all_texts = []
        for area_sections in self.boilerplate_data.values():
            if isinstance(area_sections, dict):
                for section in area_sections.values():
                    if isinstance(section, str):
                        all_texts.append(section)
            elif isinstance(area_sections, str):
                all_texts.append(area_sections)

        if all_texts:
            try:
                self.vectorizer = TfidfVectorizer(
                    max_features=5000,
                    ngram_range=(1, 2),
                    stop_words='english'
                )
                self.vectorizer.fit(all_texts)
                logger.debug("TF-IDF vectorizer initialized with boilerplate content")
            except Exception as e:
                logger.warning(f"Failed to initialize vectorizer: {e}")
                self.use_ml = False

    async def generate_crosswalk(self, parsed_rfp, boilerplate_sections: Optional[List[Dict]] = None) -> List[CrosswalkResult]:
        """
        Generate a comprehensive crosswalk between RFP requirements and FOAM capabilities.

        Args:
            parsed_rfp: ParsedRFP object from RFP parser
            boilerplate_sections: Optional list of boilerplate sections for matching

        Returns:
            List of CrosswalkResult objects
        """
        results = []

        try:
            # Process each RFP section
            tasks = []
            for rfp_section in parsed_rfp.sections:
                task = asyncio.to_thread(
                    self._match_section,
                    rfp_section,
                    boilerplate_sections
                )
                tasks.append(task)

            section_results = await asyncio.gather(*tasks, return_exceptions=True)

            for section_result in section_results:
                if isinstance(section_result, Exception):
                    logger.error(f"Error processing section: {section_result}")
                else:
                    results.extend(section_result)

            logger.info(f"Generated crosswalk with {len(results)} alignment mappings")
            return results

        except Exception as e:
            logger.error(f"Error generating crosswalk: {str(e)}", exc_info=True)
            raise

    def _match_section(self, rfp_section, boilerplate_sections: Optional[List[Dict]]) -> List[CrosswalkResult]:
        """
        Match a single RFP section against boilerplate content.

        Args:
            rfp_section: RFPSection object
            boilerplate_sections: Optional boilerplate sections

        Returns:
            List of CrosswalkResult objects for this section
        """
        results = []
        section_lower = rfp_section.name.lower()

        # Map RFP section to FOAM keyword areas
        matching_areas = self._identify_matching_areas(rfp_section.content)

        for foam_area, strength in matching_areas.items():
            # Get boilerplate content for this area
            boilerplate = self._get_boilerplate_for_area(foam_area, boilerplate_sections)

            if boilerplate:
                # Compute alignment
                similarity = self._compute_similarity(rfp_section.content, boilerplate["content"])
                tag_match = self._match_tags(
                    rfp_section.content,
                    boilerplate.get("tags", [])
                )

                alignment_score, alignment_level = self._score_alignment(similarity, tag_match)

                # Assess risk and gap
                gap_flag = alignment_level == AlignmentLevel.NONE
                risk_level = self._assess_risk(alignment_level, rfp_section.scoring_weight or 0.5)

                # Identify customization needs
                customization = self._identify_customization(
                    rfp_section.content,
                    boilerplate["content"],
                    alignment_level
                )

                # Generate recommendations
                recommendations = self._generate_recommendations(
                    CrosswalkResult(
                        rfp_requirement=rfp_section.content[:200],
                        rfp_section=rfp_section.name,
                        foam_strength=foam_area,
                        boilerplate_section=boilerplate.get("name", ""),
                        boilerplate_excerpt=boilerplate["content"][:300],
                        alignment_score=alignment_score,
                        alignment_level=alignment_level,
                        gap_flag=gap_flag,
                        risk_level=risk_level,
                        customization_needed=customization
                    )
                )

                result = CrosswalkResult(
                    rfp_requirement=rfp_section.content[:200],
                    rfp_section=rfp_section.name,
                    foam_strength=foam_area,
                    boilerplate_section=boilerplate.get("name", ""),
                    boilerplate_excerpt=boilerplate["content"][:300],
                    alignment_score=alignment_score,
                    alignment_level=alignment_level,
                    gap_flag=gap_flag,
                    risk_level=risk_level,
                    customization_needed=customization,
                    recommended_actions=recommendations,
                    confidence=similarity if self.use_ml else tag_match
                )

                results.append(result)

        return results

    def _identify_matching_areas(self, content: str) -> Dict[str, float]:
        """
        Identify which FOAM keyword areas match the given content.

        Args:
            content: Text content to analyze

        Returns:
            Dict mapping FOAM areas to strength scores (0-1)
        """
        matches = {}
        content_lower = content.lower()

        for area, keywords in FOAM_KEYWORD_MAP.items():
            # Count keyword matches
            match_count = sum(1 for keyword in keywords if keyword.lower() in content_lower)

            if match_count > 0:
                # Strength is proportion of keywords matched
                strength = min(match_count / len(keywords), 1.0)
                matches[area] = strength

        return matches

    def _get_boilerplate_for_area(self, foam_area: str, boilerplate_sections: Optional[List[Dict]]) -> Optional[Dict]:
        """
        Retrieve boilerplate content for a specific FOAM area.

        Args:
            foam_area: FOAM area name
            boilerplate_sections: Optional list of boilerplate sections

        Returns:
            Dictionary with boilerplate content or None
        """
        # Use provided boilerplate or default
        if boilerplate_sections:
            for section in boilerplate_sections:
                if section.get("area") == foam_area or foam_area in section.get("tags", []):
                    return section

        # Fallback to default boilerplate
        if foam_area in self.boilerplate_data:
            content = self.boilerplate_data[foam_area]
            if isinstance(content, str):
                return {"name": foam_area, "content": content, "tags": [foam_area]}
            elif isinstance(content, dict):
                first_section = next(iter(content.values()), None)
                if first_section:
                    return {
                        "name": foam_area,
                        "content": first_section,
                        "tags": [foam_area]
                    }

        return None

    def _compute_similarity(self, rfp_text: str, boilerplate_text: str) -> float:
        """
        Compute semantic similarity between RFP and boilerplate text.

        Args:
            rfp_text: RFP requirement text
            boilerplate_text: Boilerplate content text

        Returns:
            Similarity score (0-1)
        """
        if not self.use_ml or self.vectorizer is None:
            # Fallback to simple token overlap
            return self._simple_similarity(rfp_text, boilerplate_text)

        try:
            # Vectorize both texts
            rfp_vec = self.vectorizer.transform([rfp_text])
            boilerplate_vec = self.vectorizer.transform([boilerplate_text])

            # Compute cosine similarity
            similarity = cosine_similarity(rfp_vec, boilerplate_vec)[0][0]
            return float(similarity)

        except Exception as e:
            logger.warning(f"ML similarity computation failed: {e}; using fallback")
            return self._simple_similarity(rfp_text, boilerplate_text)

    def _simple_similarity(self, text1: str, text2: str) -> float:
        """
        Simple token-based similarity fallback.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())

        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        return len(intersection) / len(union)

    def _match_tags(self, rfp_text: str, boilerplate_tags: List[str]) -> float:
        """
        Score tag-based matches.

        Args:
            rfp_text: RFP text to check
            boilerplate_tags: Tags to match against

        Returns:
            Tag match score (0-1)
        """
        if not boilerplate_tags:
            return 0.0

        rfp_lower = rfp_text.lower()
        matched_tags = sum(1 for tag in boilerplate_tags if tag.lower() in rfp_lower)

        return matched_tags / len(boilerplate_tags)

    def _score_alignment(self, similarity: float, tag_match: float) -> Tuple[float, AlignmentLevel]:
        """
        Compute alignment score and level.

        Args:
            similarity: Similarity score (0-1)
            tag_match: Tag match score (0-1)

        Returns:
            Tuple of (alignment_score, alignment_level)
        """
        # Weighted combination
        alignment_score = (similarity * 0.6) + (tag_match * 0.4)

        if alignment_score > 0.7:
            level = AlignmentLevel.STRONG
        elif alignment_score > 0.4:
            level = AlignmentLevel.PARTIAL
        elif alignment_score > 0.2:
            level = AlignmentLevel.WEAK
        else:
            level = AlignmentLevel.NONE

        return alignment_score, level

    def _assess_risk(self, alignment_level: AlignmentLevel, section_importance: float) -> RiskLevel:
        """
        Assess risk level based on alignment and section importance.

        Args:
            alignment_level: Alignment level
            section_importance: Section scoring weight (0-1)

        Returns:
            RiskLevel (green/yellow/red)
        """
        if alignment_level == AlignmentLevel.STRONG:
            return RiskLevel.GREEN
        elif alignment_level == AlignmentLevel.PARTIAL:
            # High-weight sections with partial alignment = yellow
            return RiskLevel.YELLOW if section_importance > 0.5 else RiskLevel.GREEN
        elif alignment_level == AlignmentLevel.WEAK:
            return RiskLevel.YELLOW if section_importance <= 0.5 else RiskLevel.RED
        else:  # NONE
            return RiskLevel.RED if section_importance > 0.5 else RiskLevel.YELLOW

    def _identify_customization(self, rfp_text: str, boilerplate_text: str, alignment: AlignmentLevel) -> str:
        """
        Identify what customization is needed.

        Args:
            rfp_text: RFP requirement
            boilerplate_text: Boilerplate content
            alignment: Current alignment level

        Returns:
            Customization description
        """
        if alignment == AlignmentLevel.STRONG:
            return "Minor adjustments for RFP-specific terminology and metrics"
        elif alignment == AlignmentLevel.PARTIAL:
            return "Significant adaptation needed; supplement with additional program details"
        elif alignment == AlignmentLevel.WEAK:
            return "Major rewrite required; limited boilerplate relevance"
        else:
            return "No boilerplate match; content must be developed from scratch"

    def _generate_recommendations(self, result: CrosswalkResult) -> List[str]:
        """
        Generate actionable recommendations based on alignment result.

        Args:
            result: CrosswalkResult

        Returns:
            List of recommendations
        """
        recommendations = []

        if result.alignment_level == AlignmentLevel.STRONG:
            recommendations.append(f"Use boilerplate from '{result.boilerplate_section}' as primary content")
            recommendations.append("Adapt terminology and metrics to match RFP requirements")

        elif result.alignment_level == AlignmentLevel.PARTIAL:
            recommendations.append(f"Use boilerplate from '{result.boilerplate_section}' as foundation")
            recommendations.append("Add program-specific details to address gaps")
            recommendations.append("Include relevant outcome metrics and evaluation data")

        elif result.alignment_level == AlignmentLevel.WEAK:
            recommendations.append("Develop custom content focusing on RFP requirements")
            recommendations.append(f"Reference boilerplate from '{result.boilerplate_section}' for context")
            recommendations.append("Emphasize unique FOAM value proposition")

        else:  # NONE
            recommendations.append("No boilerplate available for this requirement")
            recommendations.append("Develop entirely custom narrative")
            recommendations.append("Consider whether FOAM programs address this requirement")

        if result.gap_flag:
            recommendations.append("FLAG: Significant gap identified; review for risk implications")

        return recommendations

    def _default_boilerplate(self) -> Dict:
        """
        Return default boilerplate content for all FOAM areas.

        Returns:
            Dictionary of default boilerplate by area
        """
        return {
            "reentry": {
                "name": "Louisiana Barracks Program",
                "content": (
                    "FOAM's Louisiana Barracks Program provides comprehensive reentry and workforce "
                    "development services for justice-involved individuals in East Baton Rouge Parish. "
                    "Our program combines case management, job readiness training, and peer mentorship "
                    "to support successful reintegration and economic mobility. Services are tailored "
                    "to address common reentry barriers including employment, housing, and social support."
                ),
                "tags": ["reentry", "workforce", "justice-involved"]
            },
            "fatherhood": {
                "name": "Responsible Fatherhood Classes",
                "content": (
                    "FOAM offers comprehensive fatherhood education through our 14-lesson NPCL curriculum, "
                    "designed to strengthen father-child relationships and promote co-parenting skills. "
                    "Classes cover communication, emotional intelligence, financial management, and "
                    "parenting best practices. Participants engage in interactive activities and peer support "
                    "to enhance engagement and accountability."
                ),
                "tags": ["fatherhood", "education", "npcl"]
            },
            "case_management": {
                "name": "Project Family Build",
                "content": (
                    "Project Family Build provides wraparound case management services that coordinate "
                    "support across FOAM programs and community partners. Our individualized Plans of Care "
                    "address family needs holistically, removing barriers to engagement and achieving "
                    "measurable outcomes in child welfare prevention, economic stability, and family "
                    "preservation. Services are delivered with cultural competency and trauma-informed practice."
                ),
                "tags": ["case_management", "wraparound", "family"]
            },
            "prevention": {
                "name": "Child Welfare Prevention",
                "content": (
                    "FOAM's prevention services strengthen protective factors in families and communities, "
                    "reducing risk for child abuse and neglect. Through family support, parenting education, "
                    "and community engagement, we build resilience and address root causes of family stress. "
                    "Services target vulnerable populations and employ evidence-based interventions aligned "
                    "with Louisiana child welfare standards."
                ),
                "tags": ["prevention", "child_welfare", "protective"]
            },
            "financial_literacy": {
                "name": "Financial Literacy and Economic Mobility",
                "content": (
                    "FOAM integrates financial literacy across all programs, teaching budgeting, banking, "
                    "credit management, and financial planning. Our approach empowers individuals to achieve "
                    "economic stability and build assets for long-term success. Curriculum is practical, "
                    "culturally relevant, and outcomes-focused, with tracked improvements in financial knowledge "
                    "and behaviors."
                ),
                "tags": ["financial_literacy", "economic_mobility"]
            },
            "celebration_events": {
                "name": "Celebration of Fatherhood Events",
                "content": (
                    "FOAM hosts quarterly Celebration of Fatherhood Events that bring together fathers, "
                    "children, and families for bonding, celebration, and community. These events strengthen "
                    "engagement, build social capital, and demonstrate the value of active fatherhood. "
                    "Activities are designed to be inclusive, fun, and culturally affirming."
                ),
                "tags": ["celebration", "engagement", "community"]
            }
        }
