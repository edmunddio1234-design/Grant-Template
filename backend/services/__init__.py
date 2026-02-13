"""
FOAM Grant Alignment Engine - Services Module

Exports all backend services for RFP parsing, crosswalk analysis, gap detection,
plan generation, and AI-powered content generation.
"""

from .rfp_parser import RFPParserService, ParsedRFP, RFPSection, ScoringCriterion
from .crosswalk_engine import CrosswalkEngine, CrosswalkResult
from .gap_analyzer import GapAnalyzerService, GapAnalysis, GapFinding
from .plan_generator import PlanGeneratorService, GrantPlan, PlanSection, ComplianceItem
from .ai_service import AIDraftService, AIProvider, DraftBlock

__all__ = [
    # RFP Parser
    "RFPParserService",
    "ParsedRFP",
    "RFPSection",
    "ScoringCriterion",
    # Crosswalk Engine
    "CrosswalkEngine",
    "CrosswalkResult",
    # Gap Analyzer
    "GapAnalyzerService",
    "GapAnalysis",
    "GapFinding",
    # Plan Generator
    "PlanGeneratorService",
    "GrantPlan",
    "PlanSection",
    "ComplianceItem",
    # AI Service
    "AIDraftService",
    "AIProvider",
    "DraftBlock",
]
