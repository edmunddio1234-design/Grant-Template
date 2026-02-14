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

    # System prompt for grant alignment context
    SYSTEM_PROMPT = """You are a Grant Alignment Architect for Fathers On A Mission (FOAM).

FOAM is a 501(c)(3) nonprofit in East Baton Rouge Parish, Louisiana serving fathers and families.

Core Programs:
1. Project Family Build - Case management, wraparound services, Plans of Care, barrier removal
2. Responsible Fatherhood Classes - 14-lesson NPCL curriculum, co-parenting skills, father engagement
3. Celebration of Fatherhood Events - Quarterly bonding events, community engagement
4. Louisiana Barracks Program - Reentry services for justice-involved individuals, workforce development

Key Areas:
- Reentry & Workforce Development
- Fatherhood Education & Family Engagement
- Child Welfare Prevention & Family Preservation
- Economic Mobility & Financial Literacy
- Housing Stabilization & Community Support

Core Metrics:
- 140 active fathers, ~210 children served
- Outcome targets: 80% engagement, 75% completion, 70% long-term success
- Data collection via EmpowerDB and nFORM

When generating grant content:
1. Always anchor in FOAM's institutional strengths and actual capacity
2. Use RFP-specific language, terminology, and evaluation criteria
3. Focus on measurable alignment and authentic capability, not generic grant language
4. Reference specific FOAM programs, curricula, partnerships, and outcomes
5. Connect every statement to either FOAM capability or explicit RFP requirement
6. Include relevant metrics and evidence of effectiveness
7. Maintain professional nonprofit grant language (formal, specific, outcome-focused)

Never:
- Generate generic grant language
- Make unsupported claims about FOAM's capabilities
- Ignore RFP-specific requirements or formatting
- Exceed word count targets
- Create content without clear connection to RFP requirements"""

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
                error_str = str(e).lower()

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

        raise AIServiceError(f"Failed after {self.max_retries} retries")

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
