"""
RFP Parser Service

Comprehensive RFP parsing service that extracts structured data from PDF and DOCX files.
Includes text extraction, section classification, scoring criteria extraction, and
eligibility/deadline/funding amount detection.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import asyncio

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    import pytesseract
    from PIL import Image
    import io
except ImportError:
    pytesseract = None
    Image = None


logger = logging.getLogger(__name__)


@dataclass
class ScoringCriterion:
    """Represents a single scoring criterion from an RFP."""
    section: str
    max_points: float
    description: str
    weight: Optional[float] = None


@dataclass
class RFPSection:
    """Represents a classified section within an RFP."""
    name: str
    content: str
    word_limit: Optional[int] = None
    scoring_weight: Optional[float] = None
    formatting_notes: Optional[str] = None
    required: bool = True
    page_numbers: Optional[List[int]] = None


@dataclass
class ParsedRFP:
    """Complete parsed RFP with all extracted components."""
    title: str
    funder_name: str
    sections: List[RFPSection] = field(default_factory=list)
    scoring_criteria: List[ScoringCriterion] = field(default_factory=list)
    eligibility: List[str] = field(default_factory=list)
    deadline: Optional[str] = None
    funding_amount: Optional[str] = None
    formatting_requirements: List[str] = field(default_factory=list)
    required_attachments: List[str] = field(default_factory=list)
    raw_text: str = ""
    extraction_method: str = ""
    confidence_score: float = 0.0


class RFPParserService:
    """
    Service for parsing RFP documents (PDF/DOCX) and extracting structured data.

    Handles multiple file formats, includes OCR fallback for scanned PDFs,
    and performs NLP-based section classification and requirement extraction.
    """

    # Section classification keywords
    SECTION_PATTERNS = {
        "need_statement": [
            r"need\s+statement", r"problem\s+description", r"problem\s+statement",
            r"background", r"statement\s+of\s+need", r"community\s+need"
        ],
        "organizational_capacity": [
            r"organizational\s+capacity", r"organizational\s+experience", r"organizational\s+profile",
            r"organizational\s+strength", r"qualifications", r"team\s+experience"
        ],
        "project_design": [
            r"project\s+design", r"program\s+description", r"program\s+design",
            r"project\s+narrative", r"scope\s+of\s+work", r"intervention"
        ],
        "evaluation_plan": [
            r"evaluation\s+plan", r"assessment\s+plan", r"measurement", r"outcomes",
            r"evaluation\s+method", r"performance\s+metric"
        ],
        "budget": [
            r"budget\s+narrative", r"budget\s+justification", r"budget\s+section",
            r"financial\s+narrative", r"cost\s+effectiveness"
        ],
        "sustainability": [
            r"sustainability", r"long.?term\s+vision", r"future\s+funding",
            r"continuation", r"plan\s+for\s+sustainability"
        ],
        "dei_equity": [
            r"diversity.*equity.*inclusion", r"cultural\s+competency", r"equity\s+statement",
            r"dei", r"social\s+equity", r"health\s+equity"
        ],
        "timeline": [
            r"timeline", r"work\s+plan", r"project\s+schedule", r"implementation\s+schedule",
            r"gantt", r"milestone"
        ],
        "attachments": [
            r"attachment", r"appendix", r"required\s+document", r"supporting\s+document",
            r"exhibit"
        ]
    }

    # Keyword patterns for extraction
    SCORING_PATTERNS = [
        r"(\d+)\s+point",
        r"(\d+)\s+%",
        r"maximum\s+(\d+)\s+points",
        r"total\s+(\d+)\s+point",
        r"weight\w*:\s*(\d+)",
        r"(\d+)\s+(?:point|point|%)\s+(?:available|possible)"
    ]

    WORD_LIMIT_PATTERNS = [
        r"(?:not\s+to\s+exceed|maximum|limit\s+of)\s+(\d+)\s+words?",
        r"(\d+).?word\s+(?:limit|maximum|cap|restriction)",
        r"pages?.*?(?:not\s+to\s+exceed|maximum)\s+(\d+)",
        r"limit\s+to\s+(\d+)\s+(?:words?|pages?)"
    ]

    DEADLINE_PATTERNS = [
        r"deadline[:\s]+([^,\n]+)",
        r"submit\s+(?:by|by\s+)?([A-Za-z]+\s+\d+,?\s+20\d{2})",
        r"application\s+(?:due|close)[:\s]+([^,\n]+)",
        r"due\s+date[:\s]+([^,\n]+)"
    ]

    FUNDING_PATTERNS = [
        r"\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
        r"(\d+(?:,\d{3})*(?:\.\d{2})?)\s*dollar",
        r"award[:\s]+\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
        r"total\s+(?:award|funding)[:\s]+\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)"
    ]

    FORMATTING_PATTERNS = [
        r"(?:font|typeface)[:\s]+([^\n]+?)(?:\n|$)",
        r"(?:font\s+)?size[:\s]+([^\n]+?)(?:\n|$)",
        r"margin[:\s]+([^\n]+?)(?:\n|$)",
        r"spacing[:\s]+([^\n]+?)(?:\n|$)",
        r"line\s+spacing[:\s]+([^\n]+?)(?:\n|$)"
    ]

    def __init__(self, use_ocr: bool = True):
        """
        Initialize the RFP Parser Service.

        Args:
            use_ocr: Whether to enable OCR fallback for scanned PDFs.
        """
        self.use_ocr = use_ocr and pytesseract is not None
        if use_ocr and pytesseract is None:
            logger.warning("pytesseract not available; OCR fallback disabled")

    async def parse_document(self, file_bytes: bytes, file_type: str, filename: str = "") -> ParsedRFP:
        """
        Parse an RFP document (PDF or DOCX) and extract all structured data.

        Args:
            file_bytes: Raw file bytes
            file_type: File type ('pdf' or 'docx')
            filename: Original filename for logging

        Returns:
            ParsedRFP: Structured RFP data

        Raises:
            ValueError: If file type is unsupported
            Exception: If parsing fails
        """
        try:
            file_type = file_type.lower().strip(".")

            if file_type == "pdf":
                text = await asyncio.to_thread(self._extract_text_from_pdf, file_bytes)
                extraction_method = "pdfplumber"
            elif file_type == "docx":
                text = await asyncio.to_thread(self._extract_text_from_docx, file_bytes)
                extraction_method = "python-docx"
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            if not text or len(text.strip()) < 100:
                if self.use_ocr and file_type == "pdf":
                    logger.warning("Text extraction returned minimal content; attempting OCR fallback")
                    text = await asyncio.to_thread(self._ocr_fallback, file_bytes)
                    extraction_method = "pytesseract_ocr"
                else:
                    raise ValueError("Unable to extract meaningful text from document")

            logger.info(f"Successfully extracted text ({len(text)} chars) from {filename} using {extraction_method}")

            # Run all extraction tasks in parallel
            tasks = [
                asyncio.to_thread(self._classify_sections, text),
                asyncio.to_thread(self._extract_scoring_criteria, text),
                asyncio.to_thread(self._extract_word_limits, text),
                asyncio.to_thread(self._extract_eligibility, text),
                asyncio.to_thread(self._extract_deadline, text),
                asyncio.to_thread(self._extract_funding_amount, text),
                asyncio.to_thread(self._extract_formatting_requirements, text),
                asyncio.to_thread(self._extract_attachments, text),
                asyncio.to_thread(self._extract_title_and_funder, text),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            sections = results[0] if not isinstance(results[0], Exception) else []
            scoring_criteria = results[1] if not isinstance(results[1], Exception) else []
            word_limits = results[2] if not isinstance(results[2], Exception) else {}
            eligibility = results[3] if not isinstance(results[3], Exception) else []
            deadline = results[4] if not isinstance(results[4], Exception) else None
            funding_amount = results[5] if not isinstance(results[5], Exception) else None
            formatting_reqs = results[6] if not isinstance(results[6], Exception) else []
            attachments = results[7] if not isinstance(results[7], Exception) else []
            title, funder = results[8] if not isinstance(results[8], Exception) else ("", "")

            # Apply word limits to sections
            for section in sections:
                if section.name.lower() in word_limits:
                    section.word_limit = word_limits[section.name.lower()]

            parsed_rfp = ParsedRFP(
                title=title or filename or "Untitled RFP",
                funder_name=funder or "Unknown Funder",
                sections=sections,
                scoring_criteria=scoring_criteria,
                eligibility=eligibility,
                deadline=deadline,
                funding_amount=funding_amount,
                formatting_requirements=formatting_reqs,
                required_attachments=attachments,
                raw_text=text,
                extraction_method=extraction_method,
                confidence_score=self._calculate_confidence(sections, scoring_criteria, deadline)
            )

            logger.info(
                f"Parsed RFP: {parsed_rfp.title} from {parsed_rfp.funder_name} "
                f"({len(sections)} sections, {len(scoring_criteria)} criteria, confidence: {parsed_rfp.confidence_score:.2f})"
            )

            return parsed_rfp

        except Exception as e:
            logger.error(f"Error parsing document {filename}: {str(e)}", exc_info=True)
            raise

    def _extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """
        Extract text from PDF using pdfplumber.

        Args:
            file_bytes: Raw PDF bytes

        Returns:
            Extracted text string
        """
        if pdfplumber is None:
            raise ImportError("pdfplumber is required for PDF parsing")

        try:
            import io
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text_parts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {str(e)}")
            raise

    def _extract_text_from_docx(self, file_bytes: bytes) -> str:
        """
        Extract text from DOCX using python-docx.

        Args:
            file_bytes: Raw DOCX bytes

        Returns:
            Extracted text string
        """
        if Document is None:
            raise ImportError("python-docx is required for DOCX parsing")

        try:
            import io
            doc = Document(io.BytesIO(file_bytes))
            text_parts = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"python-docx extraction failed: {str(e)}")
            raise

    def _ocr_fallback(self, file_bytes: bytes) -> str:
        """
        Extract text from PDF using OCR (pytesseract + PIL).
        Fallback for scanned/image-based PDFs.

        Args:
            file_bytes: Raw PDF bytes

        Returns:
            Extracted text string
        """
        if pytesseract is None or Image is None:
            raise ImportError("pytesseract and Pillow required for OCR")

        try:
            import io
            if not pdfplumber:
                raise ImportError("pdfplumber required for PDF to image conversion")

            text_parts = []
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    # Convert PDF page to image
                    image = page.to_image()
                    img_array = image.original

                    # Run OCR
                    text = pytesseract.image_to_string(img_array)
                    if text:
                        text_parts.append(text)

            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"OCR fallback failed: {str(e)}")
            raise

    def _classify_sections(self, text: str) -> List[RFPSection]:
        """
        Classify RFP sections using keyword pattern matching.

        Args:
            text: Full RFP text

        Returns:
            List of classified RFPSection objects
        """
        sections = []
        lines = text.split("\n")
        current_section = None
        section_content = []

        for i, line in enumerate(lines):
            line_lower = line.lower().strip()

            # Check if line matches any section header
            matched_section = None
            for section_name, patterns in self.SECTION_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, line_lower, re.IGNORECASE):
                        matched_section = section_name
                        break
                if matched_section:
                    break

            if matched_section:
                # Save previous section
                if current_section and section_content:
                    sections.append(RFPSection(
                        name=current_section,
                        content="\n".join(section_content).strip(),
                        page_numbers=[i]
                    ))

                current_section = matched_section
                section_content = [line]
            elif current_section:
                section_content.append(line)

        # Save last section
        if current_section and section_content:
            sections.append(RFPSection(
                name=current_section,
                content="\n".join(section_content).strip(),
                page_numbers=[len(lines)]
            ))

        logger.debug(f"Classified {len(sections)} sections: {[s.name for s in sections]}")
        return sections

    def _extract_scoring_criteria(self, text: str) -> List[ScoringCriterion]:
        """
        Extract scoring criteria from text using pattern matching.

        Args:
            text: Full RFP text

        Returns:
            List of ScoringCriterion objects
        """
        criteria = []

        # Find scoring sections
        scoring_section_pattern = r"(?:evaluation\s+criteria|scoring\s+criteria|point[s]?\s+possible|rubric)(.*?)(?=\n\n|\Z)"
        scoring_matches = re.finditer(scoring_section_pattern, text, re.IGNORECASE | re.DOTALL)

        for match in scoring_matches:
            scoring_text = match.group(1)

            # Look for point values with descriptions
            point_pattern = r"(.*?)\s*[:\-–]\s*(\d+)\s+(?:point|%)"
            point_matches = re.finditer(point_pattern, scoring_text)

            for point_match in point_matches:
                description = point_match.group(1).strip()
                max_points = float(point_match.group(2))

                if description and max_points > 0:
                    # Try to identify section
                    section_match = None
                    for section_name in self.SECTION_PATTERNS.keys():
                        if section_name.replace("_", " ") in description.lower():
                            section_match = section_name
                            break

                    criteria.append(ScoringCriterion(
                        section=section_match or "general",
                        max_points=max_points,
                        description=description
                    ))

        logger.debug(f"Extracted {len(criteria)} scoring criteria")
        return criteria

    def _extract_word_limits(self, text: str) -> Dict[str, int]:
        """
        Extract word limits for sections.

        Args:
            text: Full RFP text

        Returns:
            Dict mapping section names to word limits
        """
        limits = {}

        for pattern in self.WORD_LIMIT_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                word_count = int(match.group(1))
                # Try to identify which section this applies to
                start_pos = max(0, match.start() - 200)
                context = text[start_pos:match.start()].lower()

                for section_name in self.SECTION_PATTERNS.keys():
                    if section_name.replace("_", " ") in context:
                        limits[section_name] = word_count
                        break

        logger.debug(f"Extracted {len(limits)} word limits: {limits}")
        return limits

    def _extract_eligibility(self, text: str) -> List[str]:
        """
        Extract eligibility criteria.

        Args:
            text: Full RFP text

        Returns:
            List of eligibility criteria
        """
        eligibility = []

        eligibility_pattern = r"(?:eligibility|eligible|must|requirement[s]?|qualif[iy])(.*?)(?:\n\n|$)"
        matches = re.finditer(eligibility_pattern, text, re.IGNORECASE | re.DOTALL)

        for match in matches:
            criteria_text = match.group(1)
            # Split by bullet points or numbering
            items = re.split(r"[\n•\-\d\)\.]\s*", criteria_text)
            for item in items:
                item = item.strip()
                if item and len(item) > 10:
                    eligibility.append(item)

        logger.debug(f"Extracted {len(eligibility)} eligibility criteria")
        return eligibility[:10]  # Limit to 10 top criteria

    def _extract_deadline(self, text: str) -> Optional[str]:
        """
        Extract application deadline.

        Args:
            text: Full RFP text

        Returns:
            Deadline string or None
        """
        for pattern in self.DEADLINE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                deadline = match.group(1).strip()
                logger.debug(f"Extracted deadline: {deadline}")
                return deadline

        return None

    def _extract_funding_amount(self, text: str) -> Optional[str]:
        """
        Extract total funding amount.

        Args:
            text: Full RFP text

        Returns:
            Funding amount string or None
        """
        matches = []

        for pattern in self.FUNDING_PATTERNS:
            found = re.finditer(pattern, text)
            for match in found:
                amount = match.group(1).replace(",", "")
                if amount:
                    matches.append(float(amount))

        if matches:
            # Return the largest amount found (likely the total award)
            largest = max(matches)
            funding_str = f"${largest:,.2f}"
            logger.debug(f"Extracted funding amount: {funding_str}")
            return funding_str

        return None

    def _extract_formatting_requirements(self, text: str) -> List[str]:
        """
        Extract formatting requirements.

        Args:
            text: Full RFP text

        Returns:
            List of formatting requirements
        """
        requirements = []

        for pattern in self.FORMATTING_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                req = match.group(1).strip()
                if req and req not in requirements:
                    requirements.append(req)

        logger.debug(f"Extracted {len(requirements)} formatting requirements")
        return requirements

    def _extract_attachments(self, text: str) -> List[str]:
        """
        Extract required attachments and documents.

        Args:
            text: Full RFP text

        Returns:
            List of required attachments
        """
        attachments = []

        attachment_pattern = r"(?:attachment|appendix|required\s+document|supporting\s+document|exhibit)[s]?(.*?)(?:\n\n|$)"
        matches = re.finditer(attachment_pattern, text, re.IGNORECASE | re.DOTALL)

        for match in matches:
            attachment_text = match.group(1)
            items = re.split(r"[\n•\-\d\)\.]\s*", attachment_text)
            for item in items:
                item = item.strip()
                if item and len(item) > 5:
                    attachments.append(item)

        logger.debug(f"Extracted {len(attachments)} required attachments")
        return attachments[:15]  # Limit to 15 items

    def _extract_title_and_funder(self, text: str) -> Tuple[str, str]:
        """
        Extract RFP title and funder name.

        Args:
            text: Full RFP text

        Returns:
            Tuple of (title, funder)
        """
        title = ""
        funder = ""

        # Try to find title in first few lines
        lines = text.split("\n")
        for line in lines[:20]:
            line = line.strip()
            if line and len(line) > 10 and len(line) < 200:
                if "RFP" in line or "REQUEST" in line or "NOTICE" in line:
                    title = line
                    break

        # Try to find funder name
        funder_pattern = r"(?:from|by|issued\s+by|offered\s+by)[:\s]+([^,\n]+)"
        funder_match = re.search(funder_pattern, text, re.IGNORECASE)
        if funder_match:
            funder = funder_match.group(1).strip()

        return title[:200] or "Untitled RFP", funder[:100] or "Unknown Funder"

    def _calculate_confidence(self, sections: List[RFPSection],
                             criteria: List[ScoringCriterion],
                             deadline: Optional[str]) -> float:
        """
        Calculate confidence score for parsing quality.

        Args:
            sections: Extracted sections
            criteria: Extracted criteria
            deadline: Extracted deadline

        Returns:
            Confidence score (0-1)
        """
        score = 0.0

        # Sections found (max 0.4)
        score += min(len(sections) / 5, 0.4)

        # Scoring criteria found (max 0.3)
        score += min(len(criteria) / 3, 0.3)

        # Deadline found (max 0.2)
        if deadline:
            score += 0.2

        # Base confidence (max 0.1)
        score += 0.1

        return min(score, 1.0)
