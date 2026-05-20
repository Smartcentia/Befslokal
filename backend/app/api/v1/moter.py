"""API for møteplanlegging – /api/v1/moter"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Møter"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class AgendaPunkt(BaseModel):
    id: Optional[str] = None
    punkt: str
    ansvarlig: Optional[str] = None
    varighet_min: Optional[int] = None
    ferdig: bool = False

class Deltaker(BaseModel):
    email: str
    navn: Optional[str] = None
    rolle: str = "deltaker"       # ordforer | sekretaer | deltaker

class Vedtak(BaseModel):
    tekst: str
    ansvarlig: Optional[str] = None
    frist: Optional[str] = None   # ISO date string

class MoteCreate(BaseModel):
    tittel: str
    beskrivelse: Optional[str] = None
    sted: Optional[str] = None
    start_tid: datetime
    slutt_tid: Optional[datetime] = None
    mote_type: str = "internt"
    deltakere: List[Deltaker] = []
    agenda: List[AgendaPunkt] = []

class MoteUpdate(BaseModel):
    tittel: Optional[str] = None
    beskrivelse: Optional[str] = None
    sted: Optional[str] = None
    start_tid: Optional[datetime] = None
    slutt_tid: Optional[datetime] = None
    status: Optional[str] = None
    mote_type: Optional[str] = None
    deltakere: Optional[List[Deltaker]] = None
    agenda: Optional[List[AgendaPunkt]] = None
    referat: Optional[str] = None
    vedtak: Optional[List[Vedtak]] = None


# ── Hjelpefunksjoner ─────────────────────────────────────────────────────────

async def _ensure_table(db: AsyncSession) -> None:
    """Opprett tabellen hvis den ikke finnes."""
    await db.execute(text("""
        CREATE TABLE IF NOT EXISTS moter (
            mote_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tittel        VARCHAR(300) NOT NULL,
            beskrivelse   TEXT,
            sted          VARCHAR(300),
            start_tid     TIMESTAMPTZ NOT NULL,
            slutt_tid     TIMESTAMPTZ,
            status        VARCHAR(30)  DEFAULT 'planlagt',
            mote_type     VARCHAR(50)  DEFAULT 'internt',
            deltakere     JSONB        DEFAULT '[]',
            agenda        JSONB        DEFAULT '[]',
            referat       TEXT,
            vedtak        JSONB        DEFAULT '[]',
            opprettet_av  VARCHAR(255),
            opprettet_tid TIMESTAMPTZ  DEFAULT now(),
            oppdatert_tid TIMESTAMPTZ
        )
    """))
    await db.execute(text(
        "CREATE INDEX IF NOT EXISTS moter_start_tid_idx ON moter (start_tid DESC)"
    ))
    await db.commit()


def _row_to_dict(row) -> Dict[str, Any]:
    return {
        "mote_id":       str(row.mote_id),
        "tittel":        row.tittel,
        "beskrivelse":   row.beskrivelse,
        "sted":          row.sted,
        "start_tid":     row.start_tid.isoformat() if row.start_tid else None,
        "slutt_tid":     row.slutt_tid.isoformat() if row.slutt_tid else None,
        "status":        row.status,
        "mote_type":     row.mote_type,
        "deltakere":     row.deltakere or [],
        "agenda":        row.agenda or [],
        "referat":       row.referat,
        "vedtak":        row.vedtak or [],
        "opprettet_av":  row.opprettet_av,
        "opprettet_tid": row.opprettet_tid.isoformat() if row.opprettet_tid else None,
    }


# ── Endepunkter ───────────────────────────────────────────────────────────────

@router.get("/moter")
async def list_moter(
    limit: int = 50,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Hent alle møter, sortert etter dato."""
    await _ensure_table(db)
    where = "WHERE status = :s" if status_filter else ""
    params = {"s": status_filter} if status_filter else {}
    rows = (await db.execute(
        text(f"SELECT * FROM moter {where} ORDER BY start_tid DESC LIMIT :lim"),
        {**params, "lim": limit},
    )).fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/moter/{mote_id}")
async def get_mote(
    mote_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    await _ensure_table(db)
    row = (await db.execute(
        text("SELECT * FROM moter WHERE mote_id = :id"),
        {"id": mote_id},
    )).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Møte ikke funnet")
    return _row_to_dict(row)


@router.post("/moter", status_code=201)
async def create_mote(
    body: MoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    await _ensure_table(db)
    import json
    agenda_with_ids = [
        {**p.model_dump(), "id": p.id or str(uuid4())}
        for p in body.agenda
    ]
    row = (await db.execute(text("""
        INSERT INTO moter
            (tittel, beskrivelse, sted, start_tid, slutt_tid,
             mote_type, deltakere, agenda, opprettet_av)
        VALUES
            (:tittel, :beskrivelse, :sted, :start_tid, :slutt_tid,
             :mote_type, :deltakere, :agenda, :opprettet_av)
        RETURNING *
    """), {
        "tittel":       body.tittel,
        "beskrivelse":  body.beskrivelse,
        "sted":         body.sted,
        "start_tid":    body.start_tid,
        "slutt_tid":    body.slutt_tid,
        "mote_type":    body.mote_type,
        "deltakere":    json.dumps([d.model_dump() for d in body.deltakere]),
        "agenda":       json.dumps(agenda_with_ids),
        "opprettet_av": current_user.email,
    })).fetchone()
    await db.commit()
    return _row_to_dict(row)


@router.patch("/moter/{mote_id}")
async def update_mote(
    mote_id: str,
    body: MoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    await _ensure_table(db)
    import json
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Ingen felter å oppdatere")

    # Konverter lister til JSON
    for key in ("deltakere", "agenda", "vedtak"):
        if key in updates:
            updates[key] = json.dumps(updates[key])

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["mote_id"]       = mote_id
    updates["oppdatert_tid"] = datetime.now(timezone.utc)

    row = (await db.execute(
        text(f"UPDATE moter SET {set_clause}, oppdatert_tid = :oppdatert_tid WHERE mote_id = :mote_id RETURNING *"),
        updates,
    )).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Møte ikke funnet")
    await db.commit()
    return _row_to_dict(row)


@router.delete("/moter/{mote_id}", status_code=204)
async def delete_mote(
    mote_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await _ensure_table(db)
    await db.execute(text("DELETE FROM moter WHERE mote_id = :id"), {"id": mote_id})
    await db.commit()
