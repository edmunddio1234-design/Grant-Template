"""
Boilerplate Content Management Routes - Module 1

CRUD routes for managing boilerplate categories, sections, tags, and version history.
Includes full-text search, import/export, and versioning capabilities.
"""

import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, or_, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from dependencies import get_current_user
from models import (
    BoilerplateCategory,
    BoilerplateSection,
    BoilerplateVersion,
    Tag,
    BoilerplateSectionTag,
    AuditLog,
    ActionTypeEnum,
    User,
)
from schemas import (
    BoilerplateCategoryCreate,
    BoilerplateCategoryRead,
    BoilerplateSectionCreate,
    BoilerplateSectionRead,
    BoilerplateSectionUpdate,
    BoilerplateVersionRead,
    TagCreate,
    TagRead,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/boilerplate", tags=["boilerplate"])


# ============================================================================
# CATEGORY ENDPOINTS
# ============================================================================


@router.get(
    "/categories",
    response_model=PaginatedResponse[BoilerplateCategoryRead],
    summary="List all boilerplate categories",
    status_code=status.HTTP_200_OK,
)
async def list_categories(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Items to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[BoilerplateCategoryRead]:
    """
    Retrieve all boilerplate categories with pagination.

    Returns:
        PaginatedResponse: Paginated list of boilerplate categories.
    """
    try:
        # Get total count
        count_result = await db.execute(
            select(func.count()).select_from(BoilerplateCategory)
        )
        total = count_result.scalar() or 0

        # Fetch categories
        result = await db.execute(
            select(BoilerplateCategory)
            .order_by(BoilerplateCategory.display_order, BoilerplateCategory.created_at)
            .offset(skip)
            .limit(limit)
        )
        categories = result.scalars().all()

        logger.info(f"Retrieved {len(categories)} categories (skip={skip}, limit={limit})")

        return PaginatedResponse(
            total=total,
            skip=skip,
            limit=limit,
            items=[BoilerplateCategoryRead.from_orm(cat) for cat in categories],
        )
    except Exception as e:
        logger.error(f"Error listing categories: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories",
        )


@router.post(
    "/categories",
    response_model=BoilerplateCategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new boilerplate category",
)
async def create_category(
    category_data: BoilerplateCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BoilerplateCategoryRead:
    """
    Create a new boilerplate category.

    Args:
        category_data: Category creation payload.
        db: Database session.

    Returns:
        BoilerplateCategoryRead: Created category.

    Raises:
        HTTPException: If category name already exists or database error occurs.
    """
    try:
        # Check for duplicate name
        existing = await db.execute(
            select(BoilerplateCategory).where(
                BoilerplateCategory.name == category_data.name
            )
        )
        if existing.scalar_one_or_none():
            logger.warning(f"Category with name '{category_data.name}' already exists")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category with this name already exists",
            )

        # Create new category
        new_category = BoilerplateCategory(
            name=category_data.name,
            description=category_data.description,
            display_order=category_data.display_order,
        )

        db.add(new_category)
        await db.commit()
        await db.refresh(new_category)

        logger.info(f"Created category: {new_category.id} ({category_data.name})")

        return BoilerplateCategoryRead.from_orm(new_category)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating category: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category",
        )


# ============================================================================
# SECTION ENDPOINTS
# ============================================================================


@router.get(
    "/sections",
    response_model=PaginatedResponse[BoilerplateSectionRead],
    summary="List boilerplate sections with filters",
    status_code=status.HTTP_200_OK,
)
async def list_sections(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Items to return"),
    category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
    program_area: Optional[str] = Query(None, description="Filter by program area"),
    search: Optional[str] = Query(None, description="Search title and content"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[BoilerplateSectionRead]:
    """
    List boilerplate sections with advanced filtering options.

    Args:
        skip: Pagination offset.
        limit: Pagination limit.
        category_id: Filter by category.
        program_area: Filter by program area.
        search: Full-text search in title/content.
        tags: Filter by tags (OR condition).
        is_active: Filter by active status.
        db: Database session.

    Returns:
        PaginatedResponse: Paginated list of sections.
    """
    try:
        # Build filters
        filters = [BoilerplateSection.is_active == True]

        if category_id:
            filters.append(BoilerplateSection.category_id == category_id)

        if program_area:
            filters.append(BoilerplateSection.program_area == program_area)

        if is_active is not None:
            filters[0] = BoilerplateSection.is_active == is_active

        if search:
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    BoilerplateSection.section_title.ilike(search_pattern),
                    BoilerplateSection.content.ilike(search_pattern),
                )
            )

        # Build base query
        query = select(BoilerplateSection).where(and_(*filters))

        # Apply tag filter if provided
        if tags:
            query = query.join(BoilerplateSectionTag).join(Tag).where(
                Tag.name.in_(tags)
            )

        # Get total count
        count_query = select(func.count()).select_from(BoilerplateSection).where(and_(*filters))
        if tags:
            # Adjust count query for tags
            count_query = (
                select(func.count(BoilerplateSection.id.distinct()))
                .select_from(BoilerplateSection)
                .join(BoilerplateSectionTag)
                .join(Tag)
                .where(and_(and_(*filters), Tag.name.in_(tags)))
            )

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Fetch sections
        result = await db.execute(
            query.order_by(BoilerplateSection.section_title)
            .offset(skip)
            .limit(limit)
        )
        sections = result.scalars().all()

        logger.info(f"Retrieved {len(sections)} sections with filters")

        return PaginatedResponse(
            total=total,
            skip=skip,
            limit=limit,
            items=[BoilerplateSectionRead.from_orm(sec) for sec in sections],
        )
    except Exception as e:
        logger.error(f"Error listing sections: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sections",
        )


@router.get(
    "/sections/{section_id}",
    response_model=BoilerplateSectionRead,
    summary="Get a single boilerplate section with version history",
    status_code=status.HTTP_200_OK,
)
async def get_section(
    section_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BoilerplateSectionRead:
    """
    Retrieve a single boilerplate section by ID.

    Args:
        section_id: The section UUID.
        db: Database session.

    Returns:
        BoilerplateSectionRead: The section details.

    Raises:
        HTTPException: If section not found.
    """
    try:
        result = await db.execute(
            select(BoilerplateSection).where(BoilerplateSection.id == section_id)
        )
        section = result.scalar_one_or_none()

        if not section:
            logger.warning(f"Section not found: {section_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found",
            )

        logger.info(f"Retrieved section: {section_id}")

        return BoilerplateSectionRead.from_orm(section)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving section: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve section",
        )


@router.post(
    "/sections",
    response_model=BoilerplateSectionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new boilerplate section",
)
async def create_section(
    section_data: BoilerplateSectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BoilerplateSectionRead:
    """
    Create a new boilerplate section.

    Args:
        section_data: Section creation payload.
        db: Database session.

    Returns:
        BoilerplateSectionRead: Created section.

    Raises:
        HTTPException: If category not found or database error occurs.
    """
    try:
        # Verify category exists
        category = await db.get(BoilerplateCategory, str(section_data.category_id))
        if not category:
            logger.warning(f"Category not found: {section_data.category_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        # Create section
        new_section = BoilerplateSection(
            category_id=section_data.category_id,
            section_title=section_data.section_title,
            content=section_data.content,
            evidence_type=section_data.evidence_type,
            program_area=section_data.program_area,
            compliance_relevance=section_data.compliance_relevance,
            is_active=section_data.is_active,
            tags=section_data.tags or [],
            created_by=section_data.created_by,
            version=1,
        )

        db.add(new_section)
        await db.flush()

        # Create initial version record
        version = BoilerplateVersion(
            section_id=new_section.id,
            version_number=1,
            content=new_section.content,
            changed_by=section_data.created_by or "system",
            change_notes="Initial version",
        )
        db.add(version)
        await db.commit()
        await db.refresh(new_section)

        logger.info(f"Created section: {new_section.id} ({section_data.section_title})")

        return BoilerplateSectionRead.from_orm(new_section)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating section: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create section",
        )


@router.put(
    "/sections/{section_id}",
    response_model=BoilerplateSectionRead,
    status_code=status.HTTP_200_OK,
    summary="Update a boilerplate section (auto-versions)",
)
async def update_section(
    section_id: UUID,
    section_data: BoilerplateSectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BoilerplateSectionRead:
    """
    Update a boilerplate section and auto-create a new version.

    Args:
        section_id: The section UUID.
        section_data: Update payload.
        db: Database session.

    Returns:
        BoilerplateSectionRead: Updated section.

    Raises:
        HTTPException: If section not found or database error occurs.
    """
    try:
        section = await db.get(BoilerplateSection, str(section_id))
        if not section:
            logger.warning(f"Section not found: {section_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found",
            )

        # Store old content for version comparison
        old_content = section.content

        # Apply updates
        update_data = section_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(section, key, value)

        # Increment version if content changed
        if "content" in update_data:
            section.version += 1
            version = BoilerplateVersion(
                section_id=section.id,
                version_number=section.version,
                content=section.content,
                changed_by="system",
                change_notes=f"Updated content (v{section.version})",
            )
            db.add(version)

        db.add(section)
        await db.commit()
        await db.refresh(section)

        logger.info(f"Updated section: {section_id} (version={section.version})")

        return BoilerplateSectionRead.from_orm(section)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating section: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update section",
        )


@router.delete(
    "/sections/{section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a boilerplate section",
)
async def delete_section(
    section_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft delete a boilerplate section.

    Args:
        section_id: The section UUID.
        db: Database session.

    Raises:
        HTTPException: If section not found or database error occurs.
    """
    try:
        section = await db.get(BoilerplateSection, str(section_id))
        if not section:
            logger.warning(f"Section not found: {section_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found",
            )

        section.is_active = False
        db.add(section)
        await db.commit()

        logger.info(f"Soft deleted section: {section_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting section: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete section",
        )


# ============================================================================
# VERSION ENDPOINTS
# ============================================================================


@router.get(
    "/sections/{section_id}/versions",
    response_model=List[BoilerplateVersionRead],
    summary="Get version history for a section",
    status_code=status.HTTP_200_OK,
)
async def get_section_versions(
    section_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[BoilerplateVersionRead]:
    """
    Retrieve version history for a boilerplate section.

    Args:
        section_id: The section UUID.
        db: Database session.

    Returns:
        List[BoilerplateVersionRead]: Version history.

    Raises:
        HTTPException: If section not found or database error occurs.
    """
    try:
        # Verify section exists
        section = await db.get(BoilerplateSection, str(section_id))
        if not section:
            logger.warning(f"Section not found: {section_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found",
            )

        # Get versions
        result = await db.execute(
            select(BoilerplateVersion)
            .where(BoilerplateVersion.section_id == section_id)
            .order_by(BoilerplateVersion.version_number.desc())
        )
        versions = result.scalars().all()

        logger.info(f"Retrieved {len(versions)} versions for section {section_id}")

        return [BoilerplateVersionRead.from_orm(v) for v in versions]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve versions",
        )


@router.post(
    "/sections/{section_id}/restore/{version_number}",
    response_model=BoilerplateSectionRead,
    status_code=status.HTTP_200_OK,
    summary="Restore section to a specific version",
)
async def restore_section_version(
    section_id: UUID,
    version_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BoilerplateSectionRead:
    """
    Restore a boilerplate section to a previous version.

    Args:
        section_id: The section UUID.
        version_number: The version to restore to.
        db: Database session.

    Returns:
        BoilerplateSectionRead: Restored section.

    Raises:
        HTTPException: If section or version not found.
    """
    try:
        # Get section
        section = await db.get(BoilerplateSection, str(section_id))
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found",
            )

        # Get target version
        result = await db.execute(
            select(BoilerplateVersion).where(
                and_(
                    BoilerplateVersion.section_id == section_id,
                    BoilerplateVersion.version_number == version_number,
                )
            )
        )
        target_version = result.scalar_one_or_none()

        if not target_version:
            logger.warning(f"Version {version_number} not found for section {section_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found",
            )

        # Restore content
        section.content = target_version.content
        section.version = version_number
        section.last_updated = datetime.utcnow()

        db.add(section)
        await db.commit()
        await db.refresh(section)

        logger.info(f"Restored section {section_id} to version {version_number}")

        return BoilerplateSectionRead.from_orm(section)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring version: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore version",
        )


# ============================================================================
# TAG ENDPOINTS
# ============================================================================


@router.get(
    "/tags",
    response_model=List[TagRead],
    summary="List all tags",
    status_code=status.HTTP_200_OK,
)
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[TagRead]:
    """
    Retrieve all available tags.

    Args:
        db: Database session.

    Returns:
        List[TagRead]: All tags.
    """
    try:
        result = await db.execute(
            select(Tag).order_by(Tag.name)
        )
        tags = result.scalars().all()

        logger.info(f"Retrieved {len(tags)} tags")

        return [TagRead.from_orm(tag) for tag in tags]
    except Exception as e:
        logger.error(f"Error listing tags: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tags",
        )


@router.post(
    "/tags",
    response_model=TagRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tag",
)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TagRead:
    """
    Create a new tag.

    Args:
        tag_data: Tag creation payload.
        db: Database session.

    Returns:
        TagRead: Created tag.

    Raises:
        HTTPException: If tag name already exists.
    """
    try:
        # Check for duplicate
        existing = await db.execute(
            select(Tag).where(Tag.name == tag_data.name)
        )
        if existing.scalar_one_or_none():
            logger.warning(f"Tag '{tag_data.name}' already exists")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tag already exists",
            )

        new_tag = Tag(name=tag_data.name, tag_type=tag_data.tag_type)
        db.add(new_tag)
        await db.commit()
        await db.refresh(new_tag)

        logger.info(f"Created tag: {new_tag.id} ({tag_data.name})")

        return TagRead.from_orm(new_tag)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tag: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tag",
        )


# ============================================================================
# SEARCH & EXPORT/IMPORT ENDPOINTS
# ============================================================================


@router.get(
    "/search",
    response_model=PaginatedResponse[Dict[str, Any]],
    summary="Full-text search across boilerplate content",
    status_code=status.HTTP_200_OK,
)
async def search_boilerplate(
    query: str = Query(..., min_length=2, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[Dict[str, Any]]:
    """
    Perform full-text search across boilerplate sections.

    Args:
        query: Search query.
        skip: Pagination offset.
        limit: Pagination limit.
        db: Database session.

    Returns:
        PaginatedResponse: Search results.
    """
    try:
        search_pattern = f"%{query}%"

        # Count total matches
        count_result = await db.execute(
            select(func.count())
            .select_from(BoilerplateSection)
            .where(
                and_(
                    BoilerplateSection.is_active == True,
                    or_(
                        BoilerplateSection.section_title.ilike(search_pattern),
                        BoilerplateSection.content.ilike(search_pattern),
                    ),
                )
            )
        )
        total = count_result.scalar() or 0

        # Get matching sections
        result = await db.execute(
            select(BoilerplateSection)
            .where(
                and_(
                    BoilerplateSection.is_active == True,
                    or_(
                        BoilerplateSection.section_title.ilike(search_pattern),
                        BoilerplateSection.content.ilike(search_pattern),
                    ),
                )
            )
            .order_by(BoilerplateSection.section_title)
            .offset(skip)
            .limit(limit)
        )
        sections = result.scalars().all()

        items = [
            {
                "id": str(sec.id),
                "title": sec.section_title,
                "content_preview": sec.content[:200],
                "category_id": str(sec.category_id),
                "program_area": sec.program_area,
            }
            for sec in sections
        ]

        logger.info(f"Search query '{query}' returned {len(sections)} results")

        return PaginatedResponse(
            total=total,
            skip=skip,
            limit=limit,
            items=items,
        )
    except Exception as e:
        logger.error(f"Error searching boilerplate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search boilerplate",
        )


@router.get(
    "/export",
    response_model=Dict[str, Any],
    summary="Export all boilerplate as JSON",
    status_code=status.HTTP_200_OK,
)
async def export_boilerplate(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Export all boilerplate content as JSON.

    Args:
        db: Database session.

    Returns:
        Dict: JSON export with categories and sections.
    """
    try:
        # Get all categories
        cat_result = await db.execute(
            select(BoilerplateCategory).order_by(BoilerplateCategory.display_order)
        )
        categories = cat_result.scalars().all()

        # Get all active sections
        sec_result = await db.execute(
            select(BoilerplateSection).where(BoilerplateSection.is_active == True)
        )
        sections = sec_result.scalars().all()

        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "categories": [
                {
                    "id": str(cat.id),
                    "name": cat.name,
                    "description": cat.description,
                    "display_order": cat.display_order,
                }
                for cat in categories
            ],
            "sections": [
                {
                    "id": str(sec.id),
                    "category_id": str(sec.category_id),
                    "section_title": sec.section_title,
                    "content": sec.content,
                    "evidence_type": sec.evidence_type,
                    "program_area": sec.program_area,
                    "compliance_relevance": sec.compliance_relevance,
                    "tags": sec.tags,
                    "version": sec.version,
                }
                for sec in sections
            ],
        }

        logger.info(f"Exported {len(categories)} categories and {len(sections)} sections")

        return export_data
    except Exception as e:
        logger.error(f"Error exporting boilerplate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export boilerplate",
        )


@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
    summary="Import boilerplate from JSON",
)
async def import_boilerplate(
    import_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Import boilerplate content from JSON export.

    Args:
        import_data: JSON data with categories and sections.
        db: Database session.

    Returns:
        Dict: Import results with counts.
    """
    try:
        categories_imported = 0
        sections_imported = 0

        # Import categories
        for cat_data in import_data.get("categories", []):
            existing = await db.execute(
                select(BoilerplateCategory).where(
                    BoilerplateCategory.name == cat_data["name"]
                )
            )
            if not existing.scalar_one_or_none():
                category = BoilerplateCategory(
                    name=cat_data["name"],
                    description=cat_data["description"],
                    display_order=cat_data.get("display_order", 0),
                )
                db.add(category)
                categories_imported += 1

        await db.flush()

        # Import sections
        for sec_data in import_data.get("sections", []):
            # Get category ID by name
            cat_result = await db.execute(
                select(BoilerplateCategory).where(
                    BoilerplateCategory.id == sec_data["category_id"]
                )
            )
            category = cat_result.scalar_one_or_none()

            if category:
                section = BoilerplateSection(
                    category_id=category.id,
                    section_title=sec_data["section_title"],
                    content=sec_data["content"],
                    evidence_type=sec_data.get("evidence_type"),
                    program_area=sec_data.get("program_area"),
                    compliance_relevance=sec_data.get("compliance_relevance"),
                    tags=sec_data.get("tags", []),
                    version=sec_data.get("version", 1),
                )
                db.add(section)
                sections_imported += 1

        await db.commit()

        logger.info(f"Imported {categories_imported} categories and {sections_imported} sections")

        return {
            "categories_imported": categories_imported,
            "sections_imported": sections_imported,
        }
    except Exception as e:
        logger.error(f"Error importing boilerplate: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import boilerplate",
        )
