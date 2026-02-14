"""
AI Service

Integration service for optional AI-powered grant content generation using
OpenAI or Anthropic APIs. Generates structured outlines, insert blocks,
comparison statements, and alignment justifications.
"""

import logging
import asyncio
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import time

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    """Supported AI provider."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class DraftBlock:
    """AI-generated or suggested draft content block."""
    section: str
    block_type: str  # outline/insert/comparison/justification
    content: str
    source: str  # ai_generated/boilerplate/hybrid
    confidence: float
    usage_tokens: Optional[int] = None
    model: Optional[str] = None


class RateLimitError(Exception):
    """Raised when API rate limit is exceeded."""
    pass


class AIServiceError(Exception):
    """Generic AI service error."""
    pass


class AIDraftService:
    """
    Service for AI-powered grant content generation.

    Supports OpenAI and Anthropic APIs with rate limiting, error handling,
    and graceful fallback when AI is unavailable.
    """

    # System prompt with comprehensive FOAM organizational knowledge
    SYSTEM_PROMPT = """You are a Grant Alignment Architect for FOAM.

=== ORGANIZATION IDENTITY ===
Name: FOAM
Type: 501(c)(3) nonprofit, established 2017
Location: East Baton Rouge Parish, Louisiana
Service Area: Zip codes 70802, 70805, 70806, 70807, 70812
Offices: Government Street HQ + 3255 Choctaw Drive satellite office
Executive Director: Levar Robinson (10+ years experience)
Mission: "To enhance Fathers and Father Figures which will ultimately strengthen families."
Vision: "All Fathers and Father Figures are active positive role models with their children, families, and in the community."

=== THREE-PART INTEGRATED PROGRAM MODEL ===
These three components are separate but intertwined — they work holistically.

1. Project Family Build
   - Individualized Plans of Care for each father
   - Minimum 5 case management sessions per father
   - Six-phase onboarding (initial contact within 24 hours of referral)
   - Barrier removal: employment, housing referrals, document recovery (birth certificates, SSN cards, IDs)
   - Workforce development: resume building, interview coaching, job placement
   - Emergency supports: rental/utility assistance, clothing, hygiene, childcare, transportation
   - Mental health and emotional wellness referrals
   - Follow-up check-ins at 30, 60, and 90 days after closure

2. Responsible Fatherhood Classes (14-Lesson NPCL Curriculum)
   - Delivered weekly on Tuesdays in community settings and correctional facilities
   - Lessons cover: manhood, values, self-sufficiency, communication, stress management,
     fatherhood discrimination, children's needs, building self-esteem, relationships,
     conflict resolution, co-parenting/single fatherhood
   - Evidence-based NPCL (National Partners for Community Leadership) curriculum
   - Note: Use "Responsible Fatherhood Classes" in documents, NOT "NPCL" in body text

3. Celebration of Fatherhood Events (Quarterly Bonding Events)
   - 4 per year: Cooking with Dads, Father-Daughter Dance, quarterly workshops, signature events
   - Reinforce engagement and family connection

=== REENTRY & JUSTICE-INVOLVED FATHERS ===
Louisiana Barracks Program:
- 8-lesson reentry and workforce curriculum inside DPS&C facilities
- Covers: job readiness, communication, financial decision-making, legal navigation, wellness
- Fatherhood classes in Ascension Parish Jail, East Baton Rouge Jail, community settings

=== TARGET POPULATION & OUTCOMES ===
Targets: 140 fathers, ~210 children per grant year
Outcome Goals:
- 80% achieve a stability goal (employment, transportation, or documentation)
- 75% show improvement on pre/post assessments
- 70% complete full program

=== KEY DATA — EAST BATON ROUGE PARISH ===
Population: 453,022 | Child population: 101,169 (ages 0-17)
Child poverty rate: 27% | Overall poverty rate: 18.56%
Single-parent households: 44.67% | ALICE threshold: 55% of households
Racial composition: 44.1% Black, 42.0% White, 6.6% Hispanic/Latino
Among children: 53% Black, 30.6% White, 8.9% Hispanic
Child Welfare (Region 2, FFY 2024): 6,562 reports of suspected abuse/neglect,
2,656 investigations, 508 children in foster care (monthly avg)
Neglect = 78% of substantiated maltreatment statewide

=== PROTECTIVE FACTORS (Strengthening Families) ===
1. Parental Resilience → Curriculum: stress management, emotional regulation
2. Social Connections → Peer groups, bonding events, co-parenting skills
3. Knowledge of Parenting & Child Development → 14-lesson curriculum
4. Concrete Supports in Times of Need → Case management: employment, docs, resources
5. Nurturing & Attachment → Quarterly bonding events
6. Children's Social-Emotional Competence → Father modeling, family stability

=== ORGANIZATIONAL CAPACITY ===
Staff: Executive Director (10+ yrs), LCSW supervisor (25 yrs), 3 case managers (18+ yrs combined)
Data Systems: EmpowerDB (case management), nFORM (federal reporting), SharePoint, QR-code attendance
Finance: GAAP-aligned accounting with defined roles (Program Manager, Accountant, Treasurer/CFO, ED, Board)
"Treasure Room" for donated goods at office locations

=== KEY PARTNERSHIPS ===
EnvisionBR, YWCA, DCFS, Office of the District Attorney, HOPE Ministries,
Christian Outreach Center, East Baton Rouge School System, Capital Area United Way,
Blue Cross Blue Shield Louisiana, Huey & Angelina Wilson Foundation, Lamar Family Foundation

=== GRANT PORTFOLIO ===
70 submissions (2023-2025), ~$5.7M requested, ~$670K awarded
Key funders: Act 461 ($200K), Wilson Foundation ($100K+$50K), Mayor's NOFA ($49K),
BCBSLA ($25K), Humana ($25K), Pennington ($20K), CAUW ($10K)
IMPORTANT: FOAM no longer receives DCFS TANF funding — do NOT mention in sustainability plans.

=== WRITING RULES ===
1. Write in PROSE format — paragraph-by-paragraph, NOT bullet lists
2. Use "Responsible Fatherhood Classes" (not "NPCL" in body text)
3. Use "Latino" (not "Latine")
4. Three components are "separate but intertwined"
5. Always cite specific local EBR data with sources
6. Connect every statement to FOAM capability or RFP requirement
7. Include measurable outcomes: 80%/75%/70% goals
8. Professional nonprofit grant language — formal, specific, outcome-focused
9. When RFP data is provided, address EVERY requirement point directly
10. When boilerplate content is provided, customize it to the funder — don't just copy it

Never generate generic grant language. Never make unsupported claims. Never exceed word limits."""

    def __init__(self, provider: AIProvider, api_key: str, model: str = None, max_retries: int = 3):
        """
        Initialize AI Draft Service.

        Args:
            provider: AIProvider enum (OPENAI or ANTHROPIC)
            api_key: API key for selected provider
            model: Optional model override
            max_retries: Number of retries on failure

        Raises:
            ValueError: If provider is unsupported or api_key is empty
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        self.provider = provider
        self.api_key = api_key
        self.max_retries = max_retries
        self.rate_limit_wait = 1  # Start with 1 second backoff

        # Initialize client based on provider
        if provider == AIProvider.OPENAI:
            try:
                import openai
                self.async_client = openai.AsyncOpenAI(api_key=api_key)
                self.sync_client = openai.OpenAI(api_key=api_key)
                self.model = model or "gpt-4o"
            except ImportError:
                raise ImportError("openai package required for OpenAI provider")
        elif provider == AIProvider.ANTHROPIC:
            try:
                import anthropic
                self.async_client = anthropic.AsyncAnthropic(api_key=api_key)
                self.sync_client = anthropic.Anthropic(api_key=api_key)
                self.model = model or "claude-sonnet-4-20250514"
            except ImportError:
                raise ImportError("anthropic package required for Anthropic provider")
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")

        logger.info(f"Initialized AI service: {provider.value} ({self.model})")

    async def generate_section_outline(self, section, context: Dict) -> str:
        """
        Generate a structured outline for a grant section.

        Args:
            section: PlanSection object
            context: Additional context dictionary

        Returns:
            Outline as formatted string

        Raises:
            AIServiceError: If generation fails
        """
        try:
            prompt = f"""Generate a detailed outline for a grant application section.

Section Title: {section.title}
Word Count Target: {section.word_count_target}
Alignment Status: {section.alignment_status}
Scoring Weight: {section.scoring_weight or 'Not specified'}

Context:
{json.dumps(context, indent=2)}

Requirements:
1. Provide 3-5 main headings/subsections
2. Include bullet points for each subsection
3. Ensure outline maps to RFP requirements
4. Consider FOAM's programs and capabilities in each point
5. Keep the outline concise and actionable

Format as a clear, hierarchical outline ready for writer reference."""

            content = await self._call_api([
                {"role": "user", "content": prompt}
            ])

            return content

        except Exception as e:
            logger.error(f"Error generating section outline: {str(e)}")
            raise AIServiceError(f"Failed to generate outline: {str(e)}")

    async def generate_insert_block(self, boilerplate_text: str, rfp_requirement: str) -> DraftBlock:
        """
        Generate an insert block from boilerplate adapted to RFP requirement.

        Args:
            boilerplate_text: Existing boilerplate content
            rfp_requirement: Specific RFP requirement

        Returns:
            DraftBlock with suggested content

        Raises:
            AIServiceError: If generation fails
        """
        try:
            prompt = f"""Adapt the following boilerplate text to meet this RFP requirement.

BOILERPLATE:
{boilerplate_text}

RFP REQUIREMENT:
{rfp_requirement}

Task:
1. Adapt the boilerplate language to directly address the RFP requirement
2. Maintain FOAM's institutional voice and specific program details
3. Add RFP-specific terminology and metrics
4. Keep content concise and evidence-based
5. Do not exceed 300 words

Provide the adapted text as a single coherent paragraph."""

            content = await self._call_api([
                {"role": "user", "content": prompt}
            ])

            block = DraftBlock(
                section="insert",
                block_type="insert",
                content=content,
                source="ai_generated",
                confidence=0.85,
                model=self.model
            )

            return block

        except Exception as e:
            logger.error(f"Error generating insert block: {str(e)}")
            raise AIServiceError(f"Failed to generate insert block: {str(e)}")

    async def generate_comparison_statement(self, foam_capability: str, rfp_requirement: str) -> str:
        """
        Generate a statement comparing FOAM's capability to RFP requirement.

        Args:
            foam_capability: Description of FOAM's capability
            rfp_requirement: Description of RFP requirement

        Returns:
            Comparison statement

        Raises:
            AIServiceError: If generation fails
        """
        try:
            prompt = f"""Write a comparison statement showing how FOAM's capability aligns with an RFP requirement.

FOAM CAPABILITY:
{foam_capability}

RFP REQUIREMENT:
{rfp_requirement}

Task:
1. Show specific alignment between capability and requirement
2. Highlight unique aspects of FOAM's approach
3. Include relevant metrics or outcomes
4. Use professional grant-writing language
5. Keep to 2-3 sentences max

Write the comparison as a standalone statement ready for inclusion in a grant narrative."""

            content = await self._call_api([
                {"role": "user", "content": prompt}
            ])

            return content

        except Exception as e:
            logger.error(f"Error generating comparison statement: {str(e)}")
            raise AIServiceError(f"Failed to generate comparison: {str(e)}")

    async def generate_alignment_justification(self, crosswalk_result) -> str:
        """
        Generate justification language for alignment mapping.

        Args:
            crosswalk_result: CrosswalkResult object

        Returns:
            Justification text

        Raises:
            AIServiceError: If generation fails
        """
        try:
            prompt = f"""Write a brief justification for why FOAM's program aligns with an RFP requirement.

RFP REQUIREMENT:
{crosswalk_result.rfp_requirement}

FOAM PROGRAM AREA:
{crosswalk_result.foam_strength}

BOILERPLATE EXCERPT:
{crosswalk_result.boilerplate_excerpt}

ALIGNMENT LEVEL: {crosswalk_result.alignment_level}
ALIGNMENT SCORE: {crosswalk_result.alignment_score:.2f}

Task:
1. Explain why this alignment makes sense
2. Note any gaps or required customization
3. Suggest how to strengthen the alignment if needed
4. Keep to 2-4 sentences
5. Use professional, grant-appropriate language

Write this as explanatory text for internal planning use."""

            content = await self._call_api([
                {"role": "user", "content": prompt}
            ])

            return content

        except Exception as e:
            logger.error(f"Error generating alignment justification: {str(e)}")
            raise AIServiceError(f"Failed to generate justification: {str(e)}")

    async def generate_draft_framework(self, plan) -> List[DraftBlock]:
        """
        Generate complete draft framework for entire grant application.

        Args:
            plan: GrantPlan object

        Returns:
            List of DraftBlock objects for each section

        Raises:
            AIServiceError: If generation fails
        """
        try:
            blocks = []

            # Generate blocks for each section
            tasks = []
            for section in plan.sections:
                task = asyncio.to_thread(
                    self._generate_section_block,
                    section,
                    plan
                )
                tasks.append(task)

            section_blocks = await asyncio.gather(*tasks, return_exceptions=True)

            for block in section_blocks:
                if not isinstance(block, Exception):
                    blocks.append(block)
                else:
                    logger.warning(f"Error generating section block: {block}")

            logger.info(f"Generated {len(blocks)} draft blocks for {len(plan.sections)} sections")
            return blocks

        except Exception as e:
            logger.error(f"Error generating draft framework: {str(e)}")
            raise AIServiceError(f"Failed to generate framework: {str(e)}")

    def _generate_section_block(self, section, plan: Dict) -> DraftBlock:
        """
        Generate a single section block (synchronous helper).

        Args:
            section: PlanSection object
            plan: GrantPlan object

        Returns:
            DraftBlock object
        """
        # This is called via asyncio.to_thread, so we need synchronous handling
        try:
            # Build context
            context = {
                "section_title": section.title,
                "word_count_target": section.word_count_target,
                "scoring_weight": section.scoring_weight,
                "risk_level": section.risk_level,
                "alignment_status": section.alignment_status,
                "customization_notes": section.customization_notes
            }

            prompt = f"""Generate opening paragraph for a grant application section.

SECTION: {section.title}
TARGET WORDS: {section.word_count_target}

Context: {json.dumps(context, indent=2)}

Suggested Content Blocks:
{json.dumps(section.suggested_content_blocks[:3], indent=2)}

Task:
1. Write a strong opening paragraph (100-150 words)
2. Establish context and FOAM's relevance
3. Connect to RFP evaluation criteria
4. Maintain professional grant-writing tone
5. Leave room for detailed content development

Provide only the opening paragraph, ready for inclusion in a grant draft."""

            # Synchronous API call
            content = self._call_api_sync([
                {"role": "user", "content": prompt}
            ])

            block = DraftBlock(
                section=section.title,
                block_type="outline",
                content=content,
                source="ai_generated",
                confidence=0.8,
                model=self.model
            )

            return block

        except Exception as e:
            logger.warning(f"Error generating block for {section.title}: {e}")
            return DraftBlock(
                section=section.title,
                block_type="outline",
                content=f"[Draft opening for {section.title} - AI generation failed]",
                source="fallback",
                confidence=0.0
            )

    async def _call_api(self, messages: List[Dict], max_tokens: int = 2000) -> str:
        """
        Call AI API with retry logic and rate limiting.

        Args:
            messages: Message list for API
            max_tokens: Maximum tokens in response

        Returns:
            API response content

        Raises:
            AIServiceError: If API call fails after retries
            RateLimitError: If rate limited
        """
        last_error = None
        for attempt in range(self.max_retries):
            try:
                if self.provider == AIProvider.OPENAI:
                    # OpenAI: system prompt goes in messages array
                    full_messages = [{"role": "system", "content": self.SYSTEM_PROMPT}] + messages
                    response = await self.async_client.chat.completions.create(
                        model=self.model,
                        messages=full_messages,
                        max_tokens=max_tokens,
                        temperature=0.7
                    )
                    return response.choices[0].message.content

                elif self.provider == AIProvider.ANTHROPIC:
                    response = await self.async_client.messages.create(
                        model=self.model,
                        max_tokens=max_tokens,
                        system=self.SYSTEM_PROMPT,
                        messages=messages
                    )
                    return response.content[0].text

            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                logger.error(f"AI API attempt {attempt + 1}/{self.max_retries} failed: {str(e)}")

                # Authentication / key errors — don't retry
                if any(kw in error_str for kw in ["auth", "invalid", "key", "permission", "denied", "401", "403"]):
                    logger.error(f"Authentication error — API key may be invalid: {str(e)}")
                    raise AIServiceError(f"API key error: {str(e)}")

                # Check for rate limit
                if "rate" in error_str or "quota" in error_str:
                    wait_time = min(self.rate_limit_wait * (2 ** attempt), 60)
                    logger.warning(f"Rate limited; waiting {wait_time}s before retry {attempt + 1}/{self.max_retries}")
                    await asyncio.sleep(wait_time)
                    self.rate_limit_wait = wait_time
                    continue

                # Check for other retryable errors
                if "timeout" in error_str or "connection" in error_str:
                    wait_time = 2 ** attempt
                    logger.warning(f"Transient error; waiting {wait_time}s before retry {attempt + 1}/{self.max_retries}")
                    await asyncio.sleep(wait_time)
                    continue

                # Non-retryable error
                logger.error(f"Non-retryable API error: {str(e)}")
                raise AIServiceError(f"API error: {str(e)}")

        raise AIServiceError(f"Failed after {self.max_retries} retries: {str(last_error)}")

    def _call_api_sync(self, messages: List[Dict], max_tokens: int = 2000) -> str:
        """
        Synchronous version of API call for use in threaded context.

        Args:
            messages: Message list for API
            max_tokens: Maximum tokens in response

        Returns:
            API response content
        """
        try:
            if self.provider == AIProvider.OPENAI:
                full_messages = [{"role": "system", "content": self.SYSTEM_PROMPT}] + messages
                response = self.sync_client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                return response.choices[0].message.content

            elif self.provider == AIProvider.ANTHROPIC:
                response = self.sync_client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=self.SYSTEM_PROMPT,
                    messages=messages
                )
                return response.content[0].text

        except Exception as e:
            logger.error(f"Sync API call failed: {str(e)}")
            raise AIServiceError(str(e))

    def _build_system_prompt(self) -> str:
        """
        Get the system prompt for FOAM grant alignment context.

        Returns:
            System prompt string
        """
        return self.SYSTEM_PROMPT
