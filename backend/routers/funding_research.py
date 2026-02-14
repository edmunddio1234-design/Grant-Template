"""
Funding Research router — nonprofit intelligence endpoints.

Provides search, org detail, filings, awards, personnel, and peers
using ProPublica and USAspending data with local DB caching.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models import User
from services.nonprofit_intelligence_service import (
    search_nonprofits,
    hydrate_org,
    hydrate_awards,
    get_org_filings,
    get_org_personnel,
    find_peers,
)
from services.nonprofit_api_client import clean_ein

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/funding-research",
    tags=["Funding Research"],
)


# ============================================================================
# SEARCH
# ============================================================================

@router.post("/search")
async def search_nonprofits_endpoint(
    query_text: Optional[str] = Query(None, alias="query"),
    state: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    ntee_code: Optional[str] = Query(None),
    min_revenue: Optional[float] = Query(None),
    max_revenue: Optional[float] = Query(None),
    limit: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search nonprofit organizations by name, EIN, location, NTEE, or revenue.
    Checks local DB first, falls back to ProPublica API if no results.
    """
    results = await search_nonprofits(
        db=db,
        query_text=query_text,
        state=state,
        city=city,
        ntee_code=ntee_code,
        min_revenue=min_revenue,
        max_revenue=max_revenue,
        limit=limit,
    )
    await db.commit()
    return {"orgs": results, "count": len(results)}


# ============================================================================
# ORG DETAIL (triggers hydration)
# ============================================================================

@router.get("/org/{ein}")
async def get_org_detail(
    ein: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get full organization profile. Hydrates from ProPublica if not cached.
    Returns org overview, filings, personnel, awards, and peers.
    """
    org = await hydrate_org(db, ein)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with EIN {ein} not found",
        )

    normalized = clean_ein(ein)

    # Fetch all related data
    filings = await get_org_filings(db, normalized)
    personnel = await get_org_personnel(db, normalized)
    awards = await hydrate_awards(db, normalized)
    peers = await find_peers(db, normalized)

    await db.commit()

    return {
        "org": org,
        "filings": filings,
        "personnel": personnel,
        "awards": awards,
        "peers": peers,
    }


# ============================================================================
# INDIVIDUAL DATA ENDPOINTS
# ============================================================================

@router.get("/org/{ein}/filings")
async def get_filings_endpoint(
    ein: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get 990 filing history for an organization."""
    # Ensure org is hydrated first
    await hydrate_org(db, ein)
    filings = await get_org_filings(db, ein)
    await db.commit()
    return {"filings": filings, "count": len(filings)}


@router.get("/org/{ein}/awards")
async def get_awards_endpoint(
    ein: str,
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get federal awards from USAspending for an organization."""
    awards = await hydrate_awards(db, ein, from_date, to_date)
    await db.commit()
    total = sum(a.get("amount", 0) or 0 for a in awards)
    return {"awards": awards, "count": len(awards), "total_amount": total}


@router.get("/org/{ein}/personnel")
async def get_personnel_endpoint(
    ein: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get officers and key personnel for an organization."""
    await hydrate_org(db, ein)
    personnel = await get_org_personnel(db, ein)
    await db.commit()
    return {"personnel": personnel, "count": len(personnel)}


@router.get("/org/{ein}/peers")
async def get_peers_endpoint(
    ein: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Find similar organizations by NTEE code, state, and revenue band."""
    peers = await find_peers(db, ein)
    await db.commit()
    return {"peers": peers, "count": len(peers)}
