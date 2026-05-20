"""
IFC-parser for BEFS
──────────────────
Mapper IFC-entiteter til Building / Floor / Space / BIMObject.

Støttede versjoner: IFC2x3, IFC4, IFC4x3 (via ifcopenshell).
Lazy import av ifcopenshell – installeres separat (ikke del av grunnmiljøet).

Mapping:
  IfcBuilding          → Building
  IfcBuildingStorey    → Floor
  IfcSpace             → Space
  IfcElement (alle)    → BIMObject (med ifc_guid + properties JSON)

Konfliktsstrategi: match på navn (case-insensitive), oppdater areal/metadata.
"""
from __future__ import annotations

import io
import logging
import tempfile
import os
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─── Dataklasser (rene Python, ingen ORM-avhengighet) ─────────────────────────

@dataclass
class ParsedSpace:
    ifc_guid: str
    name: str
    space_type: str          # room, office, kitchen, bathroom, corridor, storage, other
    area_sqm: Optional[float]
    description: Optional[str]
    floor_index: int         # indeks inn i ParsedFloor.spaces (brukes internt)

@dataclass
class ParsedFloor:
    ifc_guid: str
    name: str
    floor_number: int        # -1=kjeller, 0=bakkeplan, 1=1.etasje …
    area_sqm: Optional[float]
    spaces: list[ParsedSpace] = field(default_factory=list)

@dataclass
class ParsedBuilding:
    ifc_guid: str
    name: str
    building_code: Optional[str]
    year_built: Optional[int]
    total_area_sqm: Optional[float]
    building_type: str       # main, annex, garage
    floors: list[ParsedFloor] = field(default_factory=list)

@dataclass
class ParsedBIMObject:
    ifc_guid: str
    name: Optional[str]
    ifc_type: str            # IfcWall, IfcDoor, …
    properties: dict[str, Any]
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    pos_z: Optional[float] = None

@dataclass
class IFCParseResult:
    schema: str              # IFC2X3, IFC4, …
    project_name: str
    buildings: list[ParsedBuilding]
    bim_objects: list[ParsedBIMObject]
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)


# ─── Property-set helpers ──────────────────────────────────────────────────────

def _get_pset_value(element, pset_name: str, prop_name: str) -> Any:
    """Hent én property fra et navngitt Pset på et IFC-element."""
    try:
        for rel in getattr(element, "IsDefinedBy", []):
            if not hasattr(rel, "RelatingPropertyDefinition"):
                continue
            pdef = rel.RelatingPropertyDefinition
            if getattr(pdef, "Name", "") != pset_name:
                continue
            for prop in getattr(pdef, "HasProperties", []):
                if getattr(prop, "Name", "") == prop_name:
                    val = getattr(prop, "NominalValue", None)
                    if val is not None:
                        return getattr(val, "wrappedValue", None)
    except Exception:
        pass
    return None


def _get_quantity(element, qset_name: str, qty_name: str) -> Optional[float]:
    """Hent numerisk mengde fra et QuantitySet (Qto_*)."""
    try:
        for rel in getattr(element, "IsDefinedBy", []):
            if not hasattr(rel, "RelatingPropertyDefinition"):
                continue
            pdef = rel.RelatingPropertyDefinition
            if getattr(pdef, "Name", "") != qset_name:
                continue
            for qty in getattr(pdef, "Quantities", []):
                if getattr(qty, "Name", "") == qty_name:
                    for attr in ("LengthValue", "AreaValue", "VolumeValue", "CountValue", "WeightValue"):
                        v = getattr(qty, attr, None)
                        if v is not None:
                            return float(v)
    except Exception:
        pass
    return None


def _all_pset_values(element) -> dict[str, Any]:
    """Hent alle property-set-verdier som flat dict for BIMObject.properties."""
    result: dict[str, Any] = {}
    try:
        for rel in getattr(element, "IsDefinedBy", []):
            if not hasattr(rel, "RelatingPropertyDefinition"):
                continue
            pdef = rel.RelatingPropertyDefinition
            pset_name = getattr(pdef, "Name", "")
            for prop in getattr(pdef, "HasProperties", []):
                prop_name = getattr(prop, "Name", "")
                val = getattr(prop, "NominalValue", None)
                if val is not None:
                    key = f"{pset_name}.{prop_name}"
                    result[key] = getattr(val, "wrappedValue", str(val))
    except Exception:
        pass
    return result


# ─── Space type mapping ────────────────────────────────────────────────────────

_SPACE_TYPE_MAP = {
    "office":       "office",
    "kontor":       "office",
    "kitchen":      "kitchen",
    "kjøkken":      "kitchen",
    "bathroom":     "bathroom",
    "wc":           "bathroom",
    "toalett":      "bathroom",
    "bad":          "bathroom",
    "corridor":     "corridor",
    "korridor":     "corridor",
    "gang":         "corridor",
    "storage":      "storage",
    "lager":        "storage",
    "bod":          "storage",
    "meeting":      "office",
    "møterom":      "office",
    "bedroom":      "room",
    "soverom":      "room",
}

def _map_space_type(category: Optional[str], name: str) -> str:
    text = (category or name or "").lower()
    for key, stype in _SPACE_TYPE_MAP.items():
        if key in text:
            return stype
    return "room"


# ─── Etasje-nummer fra IFC ─────────────────────────────────────────────────────

def _storey_number(storey) -> int:
    """
    Prøver å avlede floor_number fra:
    1. Pset_BuildingStoreyCommon.ElevationOfSSLRelative
    2. Elevation-attributtet
    3. Navn-parsing ("2. etasje", "Kjeller", "U1" osv.)
    """
    # Pset
    elev = _get_pset_value(storey, "Pset_BuildingStoreyCommon", "ElevationOfSSLRelative")
    if elev is None:
        elev = getattr(storey, "Elevation", None)
    if elev is not None:
        try:
            e = float(elev)
            if e < -0.5:
                return -1
            if e < 0.5:
                return 0
            return max(1, round(e / 3.0))   # grov etasje-beregning (3 m per etasje)
        except (TypeError, ValueError):
            pass

    # Navn-parsing
    name = (getattr(storey, "Name", "") or "").lower().strip()
    if any(k in name for k in ("kjeller", "under", "u1", "b1", "basement", "souterrain")):
        return -1
    if any(k in name for k in ("bakkeplan", "ground", "erdgeschoss", "0.", "plan 0")):
        return 0
    import re
    m = re.search(r"(\d+)", name)
    if m:
        return int(m.group(1))
    return 0


# ─── Hoved-parser ─────────────────────────────────────────────────────────────

def parse_ifc(file_bytes: bytes, filename: str = "model.ifc") -> IFCParseResult:
    """
    Parser en IFC-fil (bytes) og returnerer IFCParseResult.
    Lazy import av ifcopenshell – kaster ImportError om ikke installert.
    """
    try:
        import ifcopenshell  # type: ignore  # lazy
    except ImportError:
        raise ImportError(
            "ifcopenshell er ikke installert. Kjør: pip install ifcopenshell"
        )

    warnings: list[str] = []

    # Skriv til midlertidig fil (ifcopenshell krever filbane)
    with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        model = ifcopenshell.open(tmp_path)
    finally:
        os.unlink(tmp_path)

    schema = model.schema  # "IFC2X3", "IFC4", …

    # Prosjektnavn
    projects = model.by_type("IfcProject")
    project_name = getattr(projects[0], "Name", filename) if projects else filename

    buildings_out: list[ParsedBuilding] = []
    bim_objects: list[ParsedBIMObject] = []

    # ── Bygg ──────────────────────────────────────────────────────────────────
    for ifc_building in model.by_type("IfcBuilding"):
        b_name = getattr(ifc_building, "Name", None) or "Ukjent bygg"
        b_guid = getattr(ifc_building, "GlobalId", "") or ""

        year_built_raw = _get_pset_value(ifc_building, "Pset_BuildingCommon", "YearOfConstruction")
        try:
            year_built: Optional[int] = int(year_built_raw) if year_built_raw else None
        except (ValueError, TypeError):
            year_built = None

        total_area = (
            _get_quantity(ifc_building, "Qto_BuildingBaseQuantities", "GrossFloorArea")
            or _get_quantity(ifc_building, "Qto_BuildingBaseQuantities", "FootprintArea")
        )

        b_code = _get_pset_value(ifc_building, "Pset_BuildingCommon", "BuildingID") or None

        b_type_raw = (_get_pset_value(ifc_building, "Pset_BuildingCommon", "OccupancyType") or "").lower()
        if "garage" in b_type_raw or "parkering" in b_type_raw:
            b_type = "garage"
        elif "annex" in b_type_raw or "tilbygg" in b_type_raw:
            b_type = "annex"
        else:
            b_type = "main"

        parsed_building = ParsedBuilding(
            ifc_guid=b_guid,
            name=b_name,
            building_code=b_code,
            year_built=year_built,
            total_area_sqm=total_area,
            building_type=b_type,
        )

        # ── Etasjer ───────────────────────────────────────────────────────────
        for ifc_storey in model.by_type("IfcBuildingStorey"):
            # Sjekk at storyen tilhører dette bygget
            try:
                decomposed_by = ifc_building.IsDecomposedBy
                all_storeys_in_building = []
                for rel in decomposed_by:
                    all_storeys_in_building.extend(rel.RelatedObjects)
                if ifc_storey not in all_storeys_in_building:
                    continue
            except Exception:
                pass  # faller gjennom – inkluder uansett om vi ikke kan avgjøre

            s_guid = getattr(ifc_storey, "GlobalId", "") or ""
            s_name = getattr(ifc_storey, "Name", None) or "Etasje"
            s_num = _storey_number(ifc_storey)
            s_area = _get_quantity(ifc_storey, "Qto_BuildingStoreyBaseQuantities", "GrossFloorArea")

            parsed_floor = ParsedFloor(
                ifc_guid=s_guid,
                name=s_name,
                floor_number=s_num,
                area_sqm=s_area,
            )

            # ── Rom ───────────────────────────────────────────────────────────
            for ifc_space in model.by_type("IfcSpace"):
                # Sjekk at rommet tilhører denne etasjen
                try:
                    space_storeys = []
                    for rel in getattr(ifc_space, "Decomposes", []):
                        space_storeys.append(rel.RelatingObject)
                    if ifc_storey not in space_storeys:
                        continue
                except Exception:
                    pass

                sp_guid = getattr(ifc_space, "GlobalId", "") or ""
                sp_name = getattr(ifc_space, "Name", None) or "Rom"
                sp_long = getattr(ifc_space, "LongName", None)
                sp_display = sp_long or sp_name

                sp_area = (
                    _get_quantity(ifc_space, "Qto_SpaceBaseQuantities", "GrossFloorArea")
                    or _get_quantity(ifc_space, "Qto_SpaceBaseQuantities", "NetFloorArea")
                )
                sp_category = _get_pset_value(ifc_space, "Pset_SpaceCommon", "Category")
                sp_type = _map_space_type(sp_category, sp_display)

                parsed_floor.spaces.append(ParsedSpace(
                    ifc_guid=sp_guid,
                    name=sp_display,
                    space_type=sp_type,
                    area_sqm=sp_area,
                    description=sp_category,
                    floor_index=len(parsed_floor.spaces),
                ))

            parsed_building.floors.append(parsed_floor)

        # Sorter etasjer på floor_number
        parsed_building.floors.sort(key=lambda f: f.floor_number)

        if not parsed_building.floors:
            warnings.append(f"Bygg '{b_name}': ingen etasjer funnet i IFC-filen")

        buildings_out.append(parsed_building)

    if not buildings_out:
        warnings.append("Ingen IfcBuilding-entiteter funnet. Filen inneholder kanskje bare objekter.")

    # ── BIMObjects (alle IfcElement-subklasser) ───────────────────────────────
    ELEMENT_TYPES = [
        "IfcWall", "IfcDoor", "IfcWindow", "IfcSlab", "IfcRoof",
        "IfcColumn", "IfcBeam", "IfcStair", "IfcRailing",
        "IfcFlowTerminal", "IfcSanitaryTerminal", "IfcLightFixture",
        "IfcElectricAppliance", "IfcAirTerminal", "IfcPump",
        "IfcBoiler", "IfcChiller", "IfcUnitaryEquipment",
    ]
    seen_guids: set[str] = set()
    for ifc_type in ELEMENT_TYPES:
        try:
            elements = model.by_type(ifc_type)
        except Exception:
            continue
        for el in elements:
            guid = getattr(el, "GlobalId", "") or ""
            if guid in seen_guids:
                continue
            seen_guids.add(guid)

            props = _all_pset_values(el)

            # Plassering (koordinater fra ObjectPlacement)
            px = py = pz = None
            try:
                placement = el.ObjectPlacement
                if placement and hasattr(placement, "RelativePlacement"):
                    loc = placement.RelativePlacement.Location
                    if loc:
                        coords = loc.Coordinates
                        px, py, pz = (float(c) for c in coords[:3])
            except Exception:
                pass

            bim_objects.append(ParsedBIMObject(
                ifc_guid=guid,
                name=getattr(el, "Name", None),
                ifc_type=ifc_type,
                properties=props,
                pos_x=px, pos_y=py, pos_z=pz,
            ))

    stats = {
        "buildings": len(buildings_out),
        "floors":    sum(len(b.floors) for b in buildings_out),
        "spaces":    sum(len(f.spaces) for b in buildings_out for f in b.floors),
        "bim_objects": len(bim_objects),
    }

    logger.debug(
        "IFC parsed: schema=%s project=%s buildings=%d floors=%d spaces=%d objects=%d",
        schema, project_name, stats["buildings"], stats["floors"], stats["spaces"], stats["bim_objects"]
    )

    return IFCParseResult(
        schema=schema,
        project_name=project_name,
        buildings=buildings_out,
        bim_objects=bim_objects,
        warnings=warnings,
        stats=stats,
    )
