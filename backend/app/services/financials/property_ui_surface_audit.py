"""
Eiendomsside (UI) – revisjon og feltmatrise.

Feltmatrise (primær → fallback) for eiendomssiden — se implementasjon i
enrich_property_data og frontend/app/properties/[id]/page.tsx:

| UI-felt              | DB / kilde                                              |
|----------------------|---------------------------------------------------------|
| Hjemmelshaver        | owner_name → external_data.master_data.title_holder     |
| Beskrivelse          | description (kolonne)                                   |
| Tomteareal           | land_area                                               |
| Matrikkel            | gnr, bnr, municipality_code                             |
| Org.nr (eiendom)     | org_number                                              |
| Koststed             | department_code, koststed_kode                          |
| Leiekontrakt utløp   | leiekontrakt_utlop                                      |
| Regulering           | regulation_type                                         |
| Prosjekt             | project_phase, project_comments                         |
| GL finans-kort       | Bør samsvare med valgt kostnadsår (costYear) |

CSV-rapporterer primært risiko for «0 på finans-kort» når siste GL-år er før
inneværende kalenderår, samt informative flagg for data som finnes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.core.models.property import Property as PropertyModel


def _nonempty(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, str) and not v.strip():
        return False
    return True


@dataclass
class PropertyUISurfaceRow:
    property_id: str
    name: Optional[str]
    region: Optional[str]
    issue_codes: List[str] = field(default_factory=list)
    gl_last_year: Optional[int] = None
    no_gl_in_window: bool = True
    has_owner_or_master: bool = False
    has_land_area: bool = False
    has_matrikkel: bool = False
    has_org_number: bool = False
    has_prop_description: bool = False
    has_dept_or_koststed: bool = False
    has_lease_expiry: bool = False
    has_regulation: bool = False
    has_project: bool = False


def _issue_codes(gl_last_year: Optional[int], no_gl_in_window: bool) -> List[str]:
    codes: List[str] = []
    cy = date.today().year
    if (
        not no_gl_in_window
        and gl_last_year is not None
        and gl_last_year < cy
    ):
        codes.append("ui_finance_cards_year_mismatch")
    return codes


def compute_ui_surface_row(
    p: PropertyModel,
    *,
    gl_last_year: Optional[int],
    no_gl_in_window: bool,
) -> PropertyUISurfaceRow:
    ext = p.external_data if isinstance(p.external_data, dict) else {}
    md = ext.get("master_data") if isinstance(ext.get("master_data"), dict) else {}
    has_master = _nonempty(md.get("title_holder"))
    has_owner = _nonempty(getattr(p, "owner_name", None))

    return PropertyUISurfaceRow(
        property_id=str(p.property_id),
        name=p.name,
        region=p.region,
        issue_codes=_issue_codes(gl_last_year, no_gl_in_window),
        gl_last_year=gl_last_year,
        no_gl_in_window=no_gl_in_window,
        has_owner_or_master=has_owner or has_master,
        has_land_area=_nonempty(getattr(p, "land_area", None)),
        has_matrikkel=any(
            _nonempty(getattr(p, k, None))
            for k in ("gnr", "bnr", "municipality_code")
        ),
        has_org_number=_nonempty(getattr(p, "org_number", None)),
        has_prop_description=_nonempty(getattr(p, "description", None)),
        has_dept_or_koststed=any(
            _nonempty(getattr(p, k, None))
            for k in ("department_code", "koststed_kode")
        ),
        has_lease_expiry=getattr(p, "leiekontrakt_utlop", None) is not None,
        has_regulation=_nonempty(getattr(p, "regulation_type", None)),
        has_project=_nonempty(getattr(p, "project_phase", None))
        or _nonempty(getattr(p, "project_comments", None)),
    )


async def compute_all_ui_surface_rows(
    db: AsyncSession,
    completeness_by_property_id: dict[str, tuple[Optional[int], bool]],
) -> List[PropertyUISurfaceRow]:
    """
    completeness_by_property_id: property_id -> (gl_last_year, no_gl_in_window)
    """
    r = await db.execute(select(PropertyModel))
    properties = r.scalars().all()
    out: List[PropertyUISurfaceRow] = []
    for p in properties:
        pid = str(p.property_id)
        gl_y, no_gl = completeness_by_property_id.get(pid, (None, True))
        out.append(
            compute_ui_surface_row(p, gl_last_year=gl_y, no_gl_in_window=no_gl)
        )
    return out


def ui_surface_row_to_dict(row: PropertyUISurfaceRow) -> dict:
    d = row.__dict__.copy()
    d["issue_codes"] = ";".join(row.issue_codes)
    return d
