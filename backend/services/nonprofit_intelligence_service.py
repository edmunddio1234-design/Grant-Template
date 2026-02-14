"""
Nonprofit Intelligence Service — business logic for funding research.

Handles search, hydration, caching, and peer-finding using ProPublica
and USAspending data stored in the local database.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func, delete, and_, or_, cast, Float as SAFloat
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from models import (
    NonprofitOrg,
    NonprofitFiling990,
    NonprofitPersonnel,
    NonprofitAward,
    NonprofitCache,
)
from services.nonprofit_api_client import (
    propublica_search,
    propublica_org,
    usaspending_awards,
    clean_ein,
    normalize_name,
    to_float_or_none,
)

logger = logging.getLogger(__name__)

# Cache TTLs
ORG_TTL_SECONDS = 60 * 60 * 24 * 7       # 7 days
AWARDS_TTL_SECONDS = 60 * 60 * 24 * 30    # 30 days


# ============================================================================
# CACHE HELPERS
# ============================================================================

async def get_cache(db: AsyncSession, cache_key: str):
    """Retrieve a cached payload if not expired."""
    result = await db.execute(
        select(NonprofitCache).where(NonprofitCache.cache_key == cache_key)
    )
    row = result.scalar_one_or_none()
    if not row:
        return None
    if row.expires_at < datetime.now(timezone.utc):
        return None
    return row.payload


async def set_cache(db: AsyncSession, cache_key: str, source: str, payload: dict, ttl_seconds: int):
    """Store a cache entry with TTL, upsert on conflict."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=ttl_seconds)

    stmt = pg_insert(NonprofitCache).values(
        cache_key=cache_key,
        payload=payload,
        source=source,
        ttl_seconds=ttl_seconds,
        cached_at=now,
        expires_at=expires,
    ).on_conflict_do_update(
        index_elements=["cache_key"],
        set_={
            "payload": payload,
            "source": source,
            "ttl_seconds": ttl_seconds,
            "cached_at": now,
            "expires_at": expires,
        }
    )
    await db.execute(stmt)
    await db.flush()


# ============================================================================
# SEARCH
# ============================================================================

async def search_nonprofits(
    db: AsyncSession,
    query_text: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    ntee_code: Optional[str] = None,
    min_revenue: Optional[float] = None,
    max_revenue: Optional[float] = None,
    limit: int = 25,
) -> list[dict]:
    """
    Search nonprofits in local DB first.
    If no results and query_text provided, fetch from ProPublica and store.
    """
    limit = min(limit, 100)

    # Build local DB query
    conditions = []
    if query_text:
        normalized = normalize_name(query_text)
        clean = clean_ein(query_text)
        conditions.append(
            or_(
                NonprofitOrg.ein == clean,
                NonprofitOrg.name_normalized.ilike(f"%{normalized}%"),
                NonprofitOrg.name_legal.ilike(f"%{query_text}%"),
            )
        )
    if state:
        conditions.append(NonprofitOrg.state == state.upper())
    if city:
        conditions.append(NonprofitOrg.city.ilike(city))
    if ntee_code:
        conditions.append(NonprofitOrg.ntee_code.ilike(f"{ntee_code}%"))
    if min_revenue is not None:
        conditions.append(NonprofitOrg.revenue_latest >= min_revenue)
    if max_revenue is not None:
        conditions.append(NonprofitOrg.revenue_latest <= max_revenue)

    stmt = select(NonprofitOrg)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(NonprofitOrg.revenue_latest.desc().nullslast()).limit(limit)

    result = await db.execute(stmt)
    rows = result.scalars().all()

    # If no local results and we have a text query, try ProPublica
    if not rows and query_text:
        upstream = await propublica_search(query_text)
        orgs = upstream.get("organizations", [])
        for org_data in orgs[:20]:
            ein = str(org_data.get("ein", ""))
            if not ein:
                continue
            normalized_ein = clean_ein(ein)
            name = str(org_data.get("name", "Unknown"))

            stmt_upsert = pg_insert(NonprofitOrg).values(
                ein=normalized_ein,
                name_legal=name,
                name_normalized=normalize_name(name),
                ntee_code=str(org_data.get("ntee_code", "") or ""),
                city=str(org_data.get("city", "") or ""),
                state=str(org_data.get("state", "") or ""),
                zip=str(org_data.get("zipcode", "") or ""),
                revenue_latest=to_float_or_none(org_data.get("revenue_amount")),
                updated_at=datetime.now(timezone.utc),
            ).on_conflict_do_update(
                index_elements=["ein"],
                set_={
                    "name_legal": name,
                    "name_normalized": normalize_name(name),
                    "ntee_code": str(org_data.get("ntee_code", "") or ""),
                    "city": str(org_data.get("city", "") or ""),
                    "state": str(org_data.get("state", "") or ""),
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            await db.execute(stmt_upsert)
        await db.flush()

        # Re-query local DB
        result = await db.execute(
            select(NonprofitOrg)
            .where(and_(*conditions) if conditions else True)
            .order_by(NonprofitOrg.revenue_latest.desc().nullslast())
            .limit(limit)
        )
        rows = result.scalars().all()

    return [_org_to_dict(r) for r in rows]


# ============================================================================
# HYDRATION
# ============================================================================

async def hydrate_org(db: AsyncSession, ein: str) -> Optional[dict]:
    """
    Ensure org data is in local DB, fetching from ProPublica if needed.
    Returns org dict or None.
    """
    normalized_ein = clean_ein(ein)
    cache_key = f"propublica:org:{normalized_ein}"

    # Check local DB
    result = await db.execute(
        select(NonprofitOrg).where(NonprofitOrg.ein == normalized_ein)
    )
    existing = result.scalar_one_or_none()

    # If exists and cache not expired, return it
    if existing:
        cached = await get_cache(db, cache_key)
        if cached is not None:
            return _org_to_dict(existing)
        # Org exists but cache expired — still return it but refresh in background
        # For now, just return existing data
        return _org_to_dict(existing)

    # Not in DB — fetch from ProPublica
    cached_payload = await get_cache(db, cache_key)
    if cached_payload:
        org_data = cached_payload.get("organization")
    else:
        payload = await propublica_org(normalized_ein)
        if not payload:
            return None
        org_data = payload.get("organization")
        if org_data:
            await set_cache(db, cache_key, "ProPublica", payload, ORG_TTL_SECONDS)

    if not org_data:
        return None

    # Store org
    stmt = pg_insert(NonprofitOrg).values(
        ein=normalized_ein,
        name_legal=str(org_data.get("name", "Unknown Organization")),
        name_normalized=normalize_name(str(org_data.get("name", ""))),
        ntee_code=str(org_data.get("ntee_code", "") or ""),
        subsection_code=str(org_data.get("subsection_code", "") or ""),
        ruling_year=to_float_or_none(org_data.get("ruling_year")),
        address_line1=str(org_data.get("address", "") or ""),
        city=str(org_data.get("city", "") or ""),
        state=str(org_data.get("state", "") or ""),
        zip=str(org_data.get("zipcode", "") or ""),
        mission=str(org_data.get("mission", "") or ""),
        website=None,
        revenue_latest=to_float_or_none(org_data.get("revenue_amount")),
        updated_at=datetime.now(timezone.utc),
    ).on_conflict_do_update(
        index_elements=["ein"],
        set_={
            "name_legal": str(org_data.get("name", "Unknown Organization")),
            "name_normalized": normalize_name(str(org_data.get("name", ""))),
            "ntee_code": str(org_data.get("ntee_code", "") or ""),
            "mission": str(org_data.get("mission", "") or ""),
            "revenue_latest": to_float_or_none(org_data.get("revenue_amount")),
            "updated_at": datetime.now(timezone.utc),
        }
    )
    await db.execute(stmt)

    # Store filings
    filings_data = org_data.get("filings_with_data") or []
    if isinstance(filings_data, list):
        for f in filings_data:
            tax_year = int(f.get("tax_prd_yr", 0) or 0)
            if tax_year <= 0:
                continue
            form_type = str(f.get("formtype", "990") or "990")
            filing_stmt = pg_insert(NonprofitFiling990).values(
                ein=normalized_ein,
                tax_year=tax_year,
                form_type=form_type,
                total_revenue=to_float_or_none(f.get("totrevenue")),
                total_expenses=to_float_or_none(f.get("totfuncexpns")),
                total_assets=to_float_or_none(f.get("totassetsend")),
                total_liabilities=to_float_or_none(f.get("totliabend")),
                pdf_url=str(f.get("pdf_url", "") or ""),
                source="ProPublica",
            ).on_conflict_do_update(
                constraint="uq_np_filing",
                set_={
                    "total_revenue": to_float_or_none(f.get("totrevenue")),
                    "total_expenses": to_float_or_none(f.get("totfuncexpns")),
                    "total_assets": to_float_or_none(f.get("totassetsend")),
                    "total_liabilities": to_float_or_none(f.get("totliabend")),
                    "pdf_url": str(f.get("pdf_url", "") or ""),
                }
            )
            await db.execute(filing_stmt)

    # Store personnel / officers
    officers = org_data.get("officers") or []
    if isinstance(officers, list) and officers:
        current_year = datetime.now().year - 1
        # Clear existing for this ein
        await db.execute(
            delete(NonprofitPersonnel).where(NonprofitPersonnel.ein == normalized_ein)
        )
        for p in officers:
            name = str(p.get("name", "") or "")
            if not name:
                continue
            await db.execute(
                pg_insert(NonprofitPersonnel).values(
                    ein=normalized_ein,
                    tax_year=current_year,
                    name=name,
                    title=str(p.get("title", "") or ""),
                    compensation=to_float_or_none(p.get("compensation")),
                )
            )

    await db.flush()

    # Return the stored org
    result = await db.execute(
        select(NonprofitOrg).where(NonprofitOrg.ein == normalized_ein)
    )
    org = result.scalar_one_or_none()
    return _org_to_dict(org) if org else None


async def hydrate_awards(
    db: AsyncSession,
    ein: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> list[dict]:
    """
    Ensure awards data for an EIN is in local DB.
    Fetches from USAspending if not cached.
    """
    normalized_ein = clean_ein(ein)
    cache_key = f"usaspending:awards:{normalized_ein}:{from_date or ''}:{to_date or ''}"

    # Check local DB first
    stmt = (
        select(NonprofitAward)
        .where(NonprofitAward.recipient_ein == normalized_ein)
        .order_by(NonprofitAward.action_date.desc().nullslast())
        .limit(500)
    )
    result = await db.execute(stmt)
    existing = result.scalars().all()
    if existing:
        return [_award_to_dict(a) for a in existing]

    # Check cache
    cached_payload = await get_cache(db, cache_key)
    if not cached_payload:
        payload = await usaspending_awards(
            normalized_ein,
            from_date=from_date or "2019-01-01",
            to_date=to_date or "2030-01-01",
        )
        if payload:
            await set_cache(db, cache_key, "USAspending", payload, AWARDS_TTL_SECONDS)
            cached_payload = payload

    if not cached_payload:
        return []

    # Parse and store awards
    rows = cached_payload.get("results", [])
    for r in rows:
        award_id = str(r.get("Award ID", "") or "")
        if not award_id:
            continue
        stmt_award = pg_insert(NonprofitAward).values(
            award_id=award_id,
            recipient_ein=normalized_ein,
            recipient_name=str(r.get("Recipient Name", "") or ""),
            amount=to_float_or_none(r.get("Award Amount")),
            action_date=str(r.get("Action Date", "") or ""),
            awarding_agency=str(r.get("Awarding Agency", "") or ""),
            award_type=str(r.get("Award Type", "") or ""),
            description=str(r.get("Description", "") or ""),
            recipient_city=str(r.get("Recipient City Name", "") or ""),
            recipient_state=str(r.get("Recipient State Code", "") or ""),
        ).on_conflict_do_update(
            index_elements=["award_id"],
            set_={
                "amount": to_float_or_none(r.get("Award Amount")),
                "action_date": str(r.get("Action Date", "") or ""),
                "awarding_agency": str(r.get("Awarding Agency", "") or ""),
            }
        )
        await db.execute(stmt_award)

    await db.flush()

    # Re-query
    result = await db.execute(
        select(NonprofitAward)
        .where(NonprofitAward.recipient_ein == normalized_ein)
        .order_by(NonprofitAward.action_date.desc().nullslast())
        .limit(500)
    )
    return [_award_to_dict(a) for a in result.scalars().all()]


# ============================================================================
# DETAIL & PEERS
# ============================================================================

async def get_org_filings(db: AsyncSession, ein: str) -> list[dict]:
    """Get 990 filings for an org."""
    normalized = clean_ein(ein)
    result = await db.execute(
        select(NonprofitFiling990)
        .where(NonprofitFiling990.ein == normalized)
        .order_by(NonprofitFiling990.tax_year.desc())
        .limit(20)
    )
    return [_filing_to_dict(f) for f in result.scalars().all()]


async def get_org_personnel(db: AsyncSession, ein: str) -> list[dict]:
    """Get officers/personnel for an org."""
    normalized = clean_ein(ein)
    result = await db.execute(
        select(NonprofitPersonnel)
        .where(NonprofitPersonnel.ein == normalized)
        .order_by(
            NonprofitPersonnel.tax_year.desc(),
            NonprofitPersonnel.compensation.desc().nullslast()
        )
        .limit(100)
    )
    return [_personnel_to_dict(p) for p in result.scalars().all()]


async def find_peers(db: AsyncSession, ein: str, limit: int = 50) -> list[dict]:
    """Find peer organizations: same NTEE, same state, similar revenue."""
    normalized = clean_ein(ein)
    result = await db.execute(
        select(NonprofitOrg).where(NonprofitOrg.ein == normalized)
    )
    base = result.scalar_one_or_none()
    if not base or not base.ntee_code or not base.state:
        return []

    revenue = float(base.revenue_latest or 0)
    low = max(0, revenue * 0.5)
    high = revenue * 1.5 if revenue > 0 else 1_000_000

    result = await db.execute(
        select(NonprofitOrg)
        .where(
            and_(
                NonprofitOrg.ein != normalized,
                NonprofitOrg.ntee_code == base.ntee_code,
                NonprofitOrg.state == base.state,
                NonprofitOrg.revenue_latest >= low,
                NonprofitOrg.revenue_latest <= high,
            )
        )
        .order_by(NonprofitOrg.revenue_latest.desc().nullslast())
        .limit(limit)
    )
    return [_org_to_dict(r) for r in result.scalars().all()]


# ============================================================================
# SERIALIZATION HELPERS
# ============================================================================

def _org_to_dict(org: NonprofitOrg) -> dict:
    return {
        "ein": org.ein,
        "name_legal": org.name_legal,
        "ntee_code": org.ntee_code,
        "subsection_code": org.subsection_code,
        "ruling_year": org.ruling_year,
        "address_line1": org.address_line1,
        "city": org.city,
        "state": org.state,
        "zip": org.zip,
        "mission": org.mission,
        "website": org.website,
        "revenue_latest": org.revenue_latest,
        "updated_at": org.updated_at.isoformat() if org.updated_at else None,
    }


def _filing_to_dict(f: NonprofitFiling990) -> dict:
    return {
        "id": f.id,
        "ein": f.ein,
        "tax_year": f.tax_year,
        "form_type": f.form_type,
        "total_revenue": f.total_revenue,
        "total_expenses": f.total_expenses,
        "total_assets": f.total_assets,
        "total_liabilities": f.total_liabilities,
        "pdf_url": f.pdf_url,
        "filed_date": f.filed_date,
        "source": f.source,
    }


def _personnel_to_dict(p: NonprofitPersonnel) -> dict:
    return {
        "id": p.id,
        "ein": p.ein,
        "tax_year": p.tax_year,
        "name": p.name,
        "title": p.title,
        "compensation": p.compensation,
    }


def _award_to_dict(a: NonprofitAward) -> dict:
    return {
        "award_id": a.award_id,
        "recipient_ein": a.recipient_ein,
        "recipient_name": a.recipient_name,
        "amount": a.amount,
        "action_date": a.action_date,
        "awarding_agency": a.awarding_agency,
        "award_type": a.award_type,
        "description": a.description,
        "recipient_city": a.recipient_city,
        "recipient_state": a.recipient_state,
    }
