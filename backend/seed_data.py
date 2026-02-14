"""
Database seed script for Grant Alignment Engine.

Populates the database with FOAM's institutional data, boilerplate content,
tags, and default admin user.

Usage:
    python seed_data.py
"""

import asyncio
import logging
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from database import db_manager, Base
from models import (
    BoilerplateCategory,
    BoilerplateSection,
    Tag,
    User,
    TagTypeEnum,
    EvidenceTypeEnum,
    UserRoleEnum,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_database() -> None:
    """
    Seed the database with FOAM institutional data.

    This function:
    1. Creates all tables
    2. Populates boilerplate categories and sections
    3. Creates tags
    4. Creates default admin user
    """
    logger.info("Starting database seed process...")

    try:
        # Initialize database
        await db_manager.initialize()
        await db_manager.create_all_tables()
        logger.info("Database tables created successfully")

        # Get session factory
        session_factory = db_manager.get_session_factory()

        # Seed data
        async with session_factory() as session:
            await seed_tags(session)
            await seed_boilerplate_categories_and_sections(session)
            await seed_default_users(session)

        logger.info("Database seed completed successfully")

    except Exception as e:
        logger.error(f"Error during database seeding: {e}", exc_info=True)
        raise

    finally:
        await db_manager.dispose()


async def seed_tags(session: AsyncSession) -> None:
    """
    Seed tag records.

    Creates tags for programs, funding types, evidence types, and priority areas.
    """
    logger.info("Seeding tags...")

    # Program tags
    program_tags = [
        ("Project Family Build", TagTypeEnum.PROGRAM),
        ("Responsible Fatherhood Classes", TagTypeEnum.PROGRAM),
        ("Celebration of Fatherhood Events", TagTypeEnum.PROGRAM),
        ("Louisiana Barracks Program", TagTypeEnum.PROGRAM),
    ]

    # Funding type tags
    funding_tags = [
        ("Federal Grants", TagTypeEnum.FUNDING_TYPE),
        ("State Grants", TagTypeEnum.FUNDING_TYPE),
        ("Foundation Grants", TagTypeEnum.FUNDING_TYPE),
        ("Corporate Sponsorship", TagTypeEnum.FUNDING_TYPE),
    ]

    # Evidence type tags
    evidence_tags = [
        ("Quantitative Outcomes", TagTypeEnum.EVIDENCE),
        ("Qualitative Testimonials", TagTypeEnum.EVIDENCE),
        ("Mixed Methods Evaluation", TagTypeEnum.EVIDENCE),
        ("Third-Party Evaluation", TagTypeEnum.EVIDENCE),
        ("Research-Based", TagTypeEnum.EVIDENCE),
    ]

    # Priority area tags
    priority_tags = [
        ("Father Engagement", TagTypeEnum.PRIORITY_AREA),
        ("Child Development", TagTypeEnum.PRIORITY_AREA),
        ("Family Strengthening", TagTypeEnum.PRIORITY_AREA),
        ("Community Impact", TagTypeEnum.PRIORITY_AREA),
        ("Economic Stability", TagTypeEnum.PRIORITY_AREA),
        ("Mental Health", TagTypeEnum.PRIORITY_AREA),
    ]

    # Outcome tags
    outcome_tags = [
        ("Increased Father Participation", TagTypeEnum.OUTCOME),
        ("Improved Child Development", TagTypeEnum.OUTCOME),
        ("Stronger Family Relationships", TagTypeEnum.OUTCOME),
        ("Economic Advancement", TagTypeEnum.OUTCOME),
        ("Community Leadership", TagTypeEnum.OUTCOME),
    ]

    # Metric tags
    metric_tags = [
        ("Pre/Post Assessment Scores", TagTypeEnum.METRIC),
        ("Attendance Rates", TagTypeEnum.METRIC),
        ("Program Completion", TagTypeEnum.METRIC),
        ("Behavioral Improvements", TagTypeEnum.METRIC),
        ("Family Stability Indicators", TagTypeEnum.METRIC),
    ]

    all_tags = (
        program_tags
        + funding_tags
        + evidence_tags
        + priority_tags
        + outcome_tags
        + metric_tags
    )

    for tag_name, tag_type in all_tags:
        tag = Tag(name=tag_name, tag_type=tag_type)
        session.add(tag)

    await session.commit()
    logger.info(f"Seeded {len(all_tags)} tags")


async def seed_boilerplate_categories_and_sections(session: AsyncSession) -> None:
    """
    Seed boilerplate categories and sections with FOAM content.

    Creates categories for organizational capacity, programs, evaluation, etc.,
    with realistic boilerplate content.
    """
    logger.info("Seeding boilerplate categories and sections...")

    # Define categories
    categories_data = [
        {
            "name": "Organizational Capacity",
            "description": "Content describing FOAM's organizational structure and capacity",
            "order": 1,
            "sections": [
                {
                    "title": "Organizational Mission & History",
                    "content": """
                    Fathers On A Mission (FOAM) is a 501(c)(3) nonprofit organization established in 2017,
                    dedicated to strengthening families and communities by empowering fathers to be actively
                    engaged parents and positive role models. Located in East Baton Rouge Parish, Louisiana,
                    FOAM serves 140 fathers and approximately 210 children annually through evidence-based
                    and culturally responsive programming.

                    Our mission is to create systemic change by promoting responsible fatherhood, supporting
                    positive parenting practices, and building stronger family units. We recognize that father
                    involvement is a critical protective factor for child development, family stability, and
                    community well-being.
                    """,
                    "program_area": "Organizational",
                    "evidence_type": EvidenceTypeEnum.QUALITATIVE,
                },
                {
                    "title": "Organizational Structure & Staffing",
                    "content": """
                    FOAM operates with a lean, mission-driven organizational structure. Our leadership team
                    includes a Executive Director with over 15 years of nonprofit management experience, a
                    Program Director with expertise in fatherhood programming, and support staff dedicated
                    to administrative operations and evaluation.

                    All staff members have lived experience in the communities we serve, ensuring cultural
                    competence and authentic relationships with participants. We maintain partnerships with
                    local universities, community colleges, and workforce development agencies to leverage
                    specialized expertise and expand service capacity.
                    """,
                    "program_area": "Organizational",
                    "evidence_type": EvidenceTypeEnum.QUALITATIVE,
                },
                {
                    "title": "Facilities & Infrastructure",
                    "content": """
                    FOAM maintains a central office and program delivery space located in East Baton Rouge Parish,
                    equipped with technology infrastructure for virtual programming, case management systems,
                    and secure data management. Our facilities comply with ADA accessibility standards and provide
                    a welcoming, family-friendly environment.

                    We utilize a hybrid delivery model, offering both in-person and virtual programming to maximize
                    accessibility and accommodate participants' schedules. Our technology infrastructure includes
                    video conferencing capabilities, learning management systems, and secure participant databases
                    compliant with HIPAA and data privacy standards.
                    """,
                    "program_area": "Organizational",
                    "evidence_type": EvidenceTypeEnum.QUALITATIVE,
                },
            ],
        },
        {
            "name": "Program Design & Implementation",
            "description": "Content describing FOAM's evidence-based programs",
            "order": 2,
            "sections": [
                {
                    "title": "Project Family Build Overview",
                    "content": """
                    Project Family Build (Bonding, Understanding, Involvement, Leadership, Development) is a
                    comprehensive, 12-week evidence-based curriculum delivered to at-risk fathers and their families.
                    The program integrates elements of cognitive-behavioral therapy, mentoring, and strengths-based
                    approaches to promote positive parenting and family engagement.

                    Components include: (1) Weekly father-child dyadic sessions, (2) Parenting skills workshops,
                    (3) Co-parenting relationship building, (4) Economic stability coaching, (5) Mental health
                    first aid training, and (6) Community resource navigation.

                    The curriculum is culturally adapted for African American and Latino families and delivered by
                    program facilitators with lived experience and formal training in fatherhood programming.
                    """,
                    "program_area": "Project Family Build",
                    "evidence_type": EvidenceTypeEnum.MIXED_METHODS,
                },
                {
                    "title": "Responsible Fatherhood Classes",
                    "content": """
                    Our Responsible Fatherhood Classes are monthly 4-hour workshops covering topics including:
                    parental rights and responsibilities, child development across age groups, communication skills,
                    conflict resolution, financial literacy, and healthy relationships.

                    Classes are delivered in accessible community locations (libraries, community centers, schools)
                    and include childcare and meals to reduce barriers to participation. We utilize interactive,
                    experiential learning methodologies appropriate for diverse literacy levels.

                    Participants receive certificates of completion and ongoing support through our mentoring network.
                    Classes are offered in English and Spanish to serve diverse populations.
                    """,
                    "program_area": "Responsible Fatherhood Classes",
                    "evidence_type": EvidenceTypeEnum.QUALITATIVE,
                },
                {
                    "title": "Celebration of Fatherhood Events",
                    "content": """
                    Annual Celebration of Fatherhood events are community celebrations designed to recognize the
                    positive contributions of fathers, increase visibility of responsible fatherhood in the community,
                    and provide networking and resource-sharing opportunities.

                    Events typically include: family-friendly activities, resource fairs with local service providers,
                    recognition of program graduates and community leaders, speeches from fathers about their
                    journeys, and entertainment provided by local artists.

                    These events serve as prevention and community mobilization opportunities, engaging broader
                    audiences in conversations about father involvement and family strengthening.
                    """,
                    "program_area": "Celebration of Fatherhood Events",
                    "evidence_type": EvidenceTypeEnum.QUALITATIVE,
                },
                {
                    "title": "Louisiana Barracks Program",
                    "content": """
                    The Louisiana Barracks Program is a specialized adaptation of FOAM's core curriculum for military
                    families stationed at local installations. The program addresses unique challenges faced by military
                    fathers, including deployment-related separation, military culture integration, and family
                    resilience.

                    Content is delivered in partnership with military family readiness groups and includes specialized
                    topics such as managing deployment stress, supporting spouses in dual military households, and
                    accessing military benefits and resources.

                    The program maintains a 95% completion rate among military participants and has received
                    commendation from military leadership.
                    """,
                    "program_area": "Louisiana Barracks Program",
                    "evidence_type": EvidenceTypeEnum.QUALITATIVE,
                },
            ],
        },
        {
            "name": "Evaluation & Outcomes",
            "description": "Content describing FOAM's evaluation methodologies and outcomes",
            "order": 3,
            "sections": [
                {
                    "title": "Evaluation Framework & Methodology",
                    "content": """
                    FOAM utilizes a comprehensive, mixed-methods evaluation framework informed by the outcomes model
                    for responsible fatherhood and best practices in nonprofit evaluation. Our evaluation approach
                    includes:

                    Quantitative Measures:
                    - Pre/post assessment of parenting knowledge and skills
                    - Father-child interaction quality assessments
                    - Participant demographics and program dosage
                    - Service linkage and resource utilization rates
                    - 6-month and 12-month follow-up outcome data

                    Qualitative Methods:
                    - Semi-structured interviews with participants and family members
                    - Focus groups exploring program impact and suggestions for improvement
                    - Case studies documenting participant journeys
                    - Observational data on father-child interactions

                    Data is collected by trained evaluators using standardized instruments and analysis follows
                    CEAP (Culturally Effective Evaluation) principles.
                    """,
                    "program_area": "Evaluation",
                    "evidence_type": EvidenceTypeEnum.MIXED_METHODS,
                },
                {
                    "title": "Key Outcome Indicators",
                    "content": """
                    FOAM tracks the following key outcome indicators:

                    Primary Outcomes:
                    - 75%+ of participants demonstrate increased parenting knowledge and skills (pre/post assessment)
                    - 80%+ of participants report improved relationship quality with children (qualitative)
                    - 85%+ of participants increase frequency/quality of father-child engagement (observational)
                    - 70%+ of participants establish or strengthen co-parenting partnerships

                    Secondary Outcomes:
                    - 60%+ increase in fathers' civic/community engagement
                    - 50%+ improvement in fathers' economic stability indicators
                    - 65%+ reduction in family conflict and improvement in communication
                    - Improved children's behavioral and developmental outcomes

                    Long-Term Outcomes:
                    - Sustained father engagement at 12-month follow-up (60%+)
                    - Intergenerational impact: Fathers serve as mentors/role models for other men
                    - Community-level reduction in childhood poverty and improvement in family stability
                    """,
                    "program_area": "Evaluation",
                    "evidence_type": EvidenceTypeEnum.QUANTITATIVE,
                },
                {
                    "title": "Data Collection & Management",
                    "content": """
                    FOAM maintains secure data collection and management systems compliant with HIPAA, FERPA, and
                    other applicable privacy standards. Data is collected through:

                    - EmpowerDB: Comprehensive case management and participant tracking system
                    - nFORM: Specialized data collection platform for federal program reporting
                    - REDCap: Research data capture for evaluation instruments
                    - Secure servers with role-based access controls and encryption

                    All data collectors receive training in cultural competence, trauma-informed practices, and
                    confidentiality protocols. Data quality is ensured through regular audits and oversight.

                    Evaluation data is used for continuous program improvement and informs strategic planning.
                    Results are shared transparently with participants, funders, and community partners.
                    """,
                    "program_area": "Evaluation",
                    "evidence_type": EvidenceTypeEnum.QUALITATIVE,
                },
            ],
        },
        {
            "name": "Compliance & Sustainability",
            "description": "Content addressing compliance and sustainability",
            "order": 4,
            "sections": [
                {
                    "title": "Financial Management & Compliance",
                    "content": """
                    FOAM maintains strong financial management practices and operational compliance:

                    - Annual independent audit by CPA firm specializing in nonprofits
                    - Board Finance Committee oversight of budgets and expenditures
                    - Segregation of duties and internal controls
                    - Compliance with all federal reporting requirements (Form 990, CFDA requirements)
                    - Regular staff training on grant compliance and fiscal policies

                    Our recent audit (2023) resulted in clean opinion with no findings or questioned costs.
                    We maintain a healthy operating reserve of 6 months of operating expenses, demonstrating
                    financial stability and sustainability.
                    """,
                    "program_area": "Compliance",
                    "evidence_type": EvidenceTypeEnum.QUALITATIVE,
                },
                {
                    "title": "Sustainability & Diversification Strategy",
                    "content": """
                    FOAM's sustainability strategy includes diverse revenue streams to reduce dependence on any
                    single funding source:

                    Current Funding (FY2023):
                    - 40%: Federal grants (HHS, Department of Defense)
                    - 25%: Foundation grants and corporate sponsorship
                    - 20%: State and local government contracts
                    - 15%: Individual donations and fundraising

                    Growth Strategy (2024-2026):
                    - Expand federal grant portfolio through new HRSA and SAMHSA applications
                    - Develop corporate partnership program with local employers
                    - Launch peer-to-peer fundraising campaign with alumni participants
                    - Increase fees for training and consulting services to other organizations
                    - Pursue social enterprise opportunities in workforce development

                    Our 3-year financial projections show 25% growth in total revenue while maintaining current
                    service quality and expanding capacity to serve 180 fathers annually by 2026.
                    """,
                    "program_area": "Sustainability",
                    "evidence_type": EvidenceTypeEnum.QUALITATIVE,
                },
                {
                    "title": "Cultural Competence & Equity",
                    "content": """
                    FOAM is deeply committed to cultural competence and advancing racial and ethnic equity:

                    - 90% of our staff identify as African American or Latino/Hispanic
                    - All programs explicitly incorporate cultural identity, historical context, and strengths-based approaches
                    - Program materials available in English and Spanish with reading level 6th grade or below
                    - Advisory board includes fathers with lived experience and community leaders
                    - Ongoing staff training in anti-racism, implicit bias, and culturally responsive practices
                    - Annual assessment of organizational cultural competence with external evaluators

                    We explicitly acknowledge and work to address systemic inequities affecting Black and Latino fathers
                    and families, recognizing the historical trauma and contemporary barriers they face.
                    """,
                    "program_area": "Compliance",
                    "evidence_type": EvidenceTypeEnum.QUALITATIVE,
                },
            ],
        },
    ]

    # Create categories and sections
    for cat_data in categories_data:
        category = BoilerplateCategory(
            id=uuid4(),
            name=cat_data["name"],
            description=cat_data["description"],
            display_order=cat_data["order"],
        )
        session.add(category)
        await session.flush()  # Ensure category is saved before adding sections

        for sec_data in cat_data["sections"]:
            section = BoilerplateSection(
                id=uuid4(),
                category_id=category.id,
                section_title=sec_data["title"],
                content=sec_data["content"].strip(),
                program_area=sec_data.get("program_area"),
                evidence_type=sec_data.get("evidence_type"),
                is_active=True,
                created_by="system@foamgrants.org",
            )
            session.add(section)

    await session.commit()
    total_sections = sum(len(cat["sections"]) for cat in categories_data)
    logger.info(
        f"Seeded {len(categories_data)} categories with {total_sections} sections"
    )


async def seed_default_users(session: AsyncSession) -> None:
    """
    Seed default users.

    Creates an admin user for initial system access.
    """
    logger.info("Seeding default users...")

    # Check if admin already exists
    from sqlalchemy import select

    existing = await session.execute(
        select(User).where(User.email == "admin@foamgrants.org")
    )
    if existing.scalar_one_or_none():
        logger.info("Admin user already exists, skipping user seeding")
        return

    # Create admin user
    admin_user = User(
        id=uuid4(),
        email="admin@foamgrants.org",
        name="FOAM Administrator",
        hashed_password=pwd_context.hash("ChangeMe123!"),  # Should be changed on first login
        role=UserRoleEnum.ADMIN,
        is_active=True,
    )
    session.add(admin_user)

    # Create sample grant manager user
    manager_user = User(
        id=uuid4(),
        email="manager@foamgrants.org",
        name="Grant Manager",
        hashed_password=pwd_context.hash("ChangeMe123!"),  # Should be changed on first login
        role=UserRoleEnum.GRANT_MANAGER,
        is_active=True,
    )
    session.add(manager_user)

    # Create sample reviewer user
    reviewer_user = User(
        id=uuid4(),
        email="reviewer@foamgrants.org",
        name="Grant Reviewer",
        hashed_password=pwd_context.hash("ChangeMe123!"),  # Should be changed on first login
        role=UserRoleEnum.REVIEWER,
        is_active=True,
    )
    session.add(reviewer_user)

    await session.commit()
    logger.info("Seeded 3 default users")
    logger.warning(
        "SECURITY WARNING: Default users created with temporary passwords. "
        "Change passwords immediately before production use."
    )


async def main():
    """Main entry point for seed script."""
    try:
        await seed_database()
        logger.info("✓ Database seeding completed successfully")
        print("\n" + "=" * 80)
        print("DATABASE SEEDING COMPLETE")
        print("=" * 80)
        print("\nDefault Users Created:")
        print("  Email: admin@foamgrants.org | Role: Admin")
        print("  Email: manager@foamgrants.org | Role: Grant Manager")
        print("  Email: reviewer@foamgrants.org | Role: Reviewer")
        print("\n⚠️  WARNING: Change default passwords before production use!")
        print("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"✗ Database seeding failed: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
