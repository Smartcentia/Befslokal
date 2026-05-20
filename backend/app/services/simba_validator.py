"""
SIMBA 2.1 Validator for BEFS
─────────────────────────────
Validerer en IFC-fil mot Statsbygg SIMBA 2.1-kravene for hvert av de 12 disiplinene.

Referanse: https://simba.statsbygg.no/kravene
IFC-versjon: IFC 4 (4.0.2.1)

Implementert som regel-basert Python (uten IDS/mvdXML-filer) for enkel drift.
Utvides til IDS-validering via ifctester når Statsbygg publiserer maskinlesbare IDS-filer.

Disipliner:
    ARK   – Arkitekt
    LARK  – Landskapsarkitekt
    IARK  – Interiørarkitekt
    RIB   – Rådgivende ingeniør bygg (konstruksjon)
    RIV   – Rådgivende ingeniør VVS
    RIVA  – Rådgivende ingeniør VA (vann/avløp)
    RIE   – Rådgivende ingeniør elektro
    RIAKU – Rådgivende ingeniør akustikk
    RIBR  – Rådgivende ingeniør brann
    RIS   – Rådgivende ingeniør sikkerhet
    RIM   – BIM-koordinering (alle disipliner)
    RIEN  – Rådgivende ingeniør energi
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ─── Resultatstrukturer ────────────────────────────────────────────────────────

@dataclass
class RuleResult:
    rule_id: str
    description: str
    passed: int
    failed: int
    failed_guids: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.passed + self.failed

    @property
    def pass_rate(self) -> float:
        return (self.passed / self.total * 100) if self.total else 100.0

    @property
    def status(self) -> str:
        if self.total == 0:
            return "N/A"
        if self.failed == 0:
            return "PASS"
        if self.pass_rate >= 80:
            return "WARN"
        return "FAIL"


@dataclass
class DisciplineResult:
    discipline: str
    label: str
    rules: list[RuleResult] = field(default_factory=list)

    @property
    def total_rules(self) -> int:
        return len([r for r in self.rules if r.total > 0])

    @property
    def passed_rules(self) -> int:
        return len([r for r in self.rules if r.status == "PASS"])

    @property
    def failed_rules(self) -> int:
        return len([r for r in self.rules if r.status == "FAIL"])

    @property
    def warn_rules(self) -> int:
        return len([r for r in self.rules if r.status == "WARN"])

    @property
    def na_rules(self) -> int:
        return len([r for r in self.rules if r.status == "N/A"])

    @property
    def compliance_pct(self) -> float:
        active = [r for r in self.rules if r.total > 0]
        if not active:
            return 100.0
        passed = sum(1 for r in active if r.status == "PASS")
        return passed / len(active) * 100

    @property
    def overall_status(self) -> str:
        if self.failed_rules > 0:
            return "FAIL"
        if self.warn_rules > 0:
            return "WARN"
        return "PASS"


@dataclass
class SIMBAValidationResult:
    schema: str
    project_name: str
    disciplines: list[DisciplineResult]
    warnings: list[str] = field(default_factory=list)

    @property
    def summary(self) -> dict[str, Any]:
        active = [d for d in self.disciplines if d.total_rules > 0]
        passed = sum(1 for d in active if d.overall_status == "PASS")
        failed = sum(1 for d in active if d.overall_status == "FAIL")
        warn   = sum(1 for d in active if d.overall_status == "WARN")
        na     = sum(1 for d in self.disciplines if d.total_rules == 0)
        return {
            "disciplines_checked": len(active),
            "disciplines_na":      na,
            "disciplines_passed":  passed,
            "disciplines_warned":  warn,
            "disciplines_failed":  failed,
        }


# ─── Pset-hjelpere (gjenbruker logikk fra ifc_parser) ─────────────────────────

def _pset(element, pset_name: str, prop_name: str) -> Any:
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


def _qty(element, qset_name: str, qty_name: str) -> Optional[float]:
    try:
        for rel in getattr(element, "IsDefinedBy", []):
            if not hasattr(rel, "RelatingPropertyDefinition"):
                continue
            pdef = rel.RelatingPropertyDefinition
            if getattr(pdef, "Name", "") != qset_name:
                continue
            for qty in getattr(pdef, "Quantities", []):
                if getattr(qty, "Name", "") == qty_name:
                    for attr in ("AreaValue", "LengthValue", "VolumeValue", "CountValue"):
                        v = getattr(qty, attr, None)
                        if v is not None:
                            return float(v)
    except Exception:
        pass
    return None


def _has_name(el) -> bool:
    return bool(getattr(el, "Name", None))


def _has_guid(el) -> bool:
    return bool(getattr(el, "GlobalId", None))


def _has_material(el) -> bool:
    try:
        for rel in getattr(el, "HasAssociations", []):
            if rel.is_a("IfcRelAssociatesMaterial"):
                return True
    except Exception:
        pass
    return False


# ─── Regelkjøring ─────────────────────────────────────────────────────────────

def _check_elements(
    model,
    ifc_type: str,
    rule_id: str,
    description: str,
    checker: Callable,
) -> RuleResult:
    """Kjør checker på alle elementer av typen; teller pass/fail."""
    try:
        elements = model.by_type(ifc_type)
    except Exception:
        return RuleResult(rule_id=rule_id, description=description, passed=0, failed=0)

    passed = failed = 0
    failed_guids: list[str] = []
    for el in elements:
        try:
            ok = checker(el)
        except Exception:
            ok = False
        if ok:
            passed += 1
        else:
            failed += 1
            guid = getattr(el, "GlobalId", None)
            if guid and len(failed_guids) < 20:   # maks 20 eksempler
                failed_guids.append(guid)

    return RuleResult(
        rule_id=rule_id,
        description=description,
        passed=passed,
        failed=failed,
        failed_guids=failed_guids,
    )


# ─── Disiplin-regler ──────────────────────────────────────────────────────────

def _validate_rim(model) -> DisciplineResult:
    """RIM – BIM-koordinering: gjelder alle disipliner."""
    d = DisciplineResult(discipline="RIM", label="BIM-koordinering")

    # Alle IfcElement-instanser skal ha GlobalId og Name
    ELEMENT_TYPES = [
        "IfcWall", "IfcDoor", "IfcWindow", "IfcSlab", "IfcColumn",
        "IfcBeam", "IfcRoof", "IfcStair", "IfcSpace",
    ]
    guid_passed = guid_failed = 0
    name_passed = name_failed = 0
    guid_fails: list[str] = []
    name_fails: list[str] = []
    for ifc_type in ELEMENT_TYPES:
        try:
            els = model.by_type(ifc_type)
        except Exception:
            continue
        for el in els:
            g = getattr(el, "GlobalId", None)
            n = getattr(el, "Name", None)
            if g:
                guid_passed += 1
            else:
                guid_failed += 1
                if len(guid_fails) < 20:
                    guid_fails.append(f"{ifc_type}:no-guid")
            if n:
                name_passed += 1
            else:
                name_failed += 1
                if n is None and g and len(name_fails) < 20:
                    name_fails.append(g)

    d.rules.append(RuleResult(
        rule_id="RIM-01",
        description="Alle elementer har GlobalId (GUID)",
        passed=guid_passed, failed=guid_failed, failed_guids=guid_fails,
    ))
    d.rules.append(RuleResult(
        rule_id="RIM-02",
        description="Alle elementer har Name",
        passed=name_passed, failed=name_failed, failed_guids=name_fails,
    ))

    # IfcProject: Name + Phase
    projects = model.by_type("IfcProject")
    if projects:
        proj = projects[0]
        d.rules.append(RuleResult(
            rule_id="RIM-03",
            description="IfcProject har Name",
            passed=1 if getattr(proj, "Name", None) else 0,
            failed=0 if getattr(proj, "Name", None) else 1,
        ))
        d.rules.append(RuleResult(
            rule_id="RIM-04",
            description="IfcProject har Phase",
            passed=1 if getattr(proj, "Phase", None) else 0,
            failed=0 if getattr(proj, "Phase", None) else 1,
        ))
    return d


def _validate_ark(model) -> DisciplineResult:
    """ARK – Arkitekt."""
    d = DisciplineResult(discipline="ARK", label="Arkitekt")

    # IfcBuilding: BuildingID + YearOfConstruction
    d.rules.append(_check_elements(model, "IfcBuilding", "ARK-01",
        "IfcBuilding har Pset_BuildingCommon.BuildingID",
        lambda el: bool(_pset(el, "Pset_BuildingCommon", "BuildingID"))))
    d.rules.append(_check_elements(model, "IfcBuilding", "ARK-02",
        "IfcBuilding har Pset_BuildingCommon.YearOfConstruction",
        lambda el: bool(_pset(el, "Pset_BuildingCommon", "YearOfConstruction"))))

    # IfcBuildingStorey: Name + Elevation
    d.rules.append(_check_elements(model, "IfcBuildingStorey", "ARK-03",
        "IfcBuildingStorey har Name",
        _has_name))
    d.rules.append(_check_elements(model, "IfcBuildingStorey", "ARK-04",
        "IfcBuildingStorey har Elevation-attributt",
        lambda el: getattr(el, "Elevation", None) is not None))

    # IfcSpace: Name + NetFloorArea + Category
    d.rules.append(_check_elements(model, "IfcSpace", "ARK-05",
        "IfcSpace har Name",
        _has_name))
    d.rules.append(_check_elements(model, "IfcSpace", "ARK-06",
        "IfcSpace har Qto_SpaceBaseQuantities.NetFloorArea eller GrossFloorArea",
        lambda el: (
            _qty(el, "Qto_SpaceBaseQuantities", "NetFloorArea") is not None or
            _qty(el, "Qto_SpaceBaseQuantities", "GrossFloorArea") is not None
        )))
    d.rules.append(_check_elements(model, "IfcSpace", "ARK-07",
        "IfcSpace har Pset_SpaceCommon.Category",
        lambda el: bool(_pset(el, "Pset_SpaceCommon", "Category"))))

    # IfcDoor: IsExternal
    d.rules.append(_check_elements(model, "IfcDoor", "ARK-08",
        "IfcDoor har Pset_DoorCommon.IsExternal",
        lambda el: _pset(el, "Pset_DoorCommon", "IsExternal") is not None))

    # IfcWindow: IsExternal
    d.rules.append(_check_elements(model, "IfcWindow", "ARK-09",
        "IfcWindow har Pset_WindowCommon.IsExternal",
        lambda el: _pset(el, "Pset_WindowCommon", "IsExternal") is not None))

    return d


def _validate_rib(model) -> DisciplineResult:
    """RIB – Konstruksjon."""
    d = DisciplineResult(discipline="RIB", label="Konstruksjon")

    # IfcColumn: Name + Material + LoadBearing
    d.rules.append(_check_elements(model, "IfcColumn", "RIB-01",
        "IfcColumn har Name", _has_name))
    d.rules.append(_check_elements(model, "IfcColumn", "RIB-02",
        "IfcColumn har material-assosiasjon", _has_material))

    # IfcBeam: Name + Material
    d.rules.append(_check_elements(model, "IfcBeam", "RIB-03",
        "IfcBeam har Name", _has_name))
    d.rules.append(_check_elements(model, "IfcBeam", "RIB-04",
        "IfcBeam har material-assosiasjon", _has_material))

    # IfcSlab: LoadBearing + IsExternal
    d.rules.append(_check_elements(model, "IfcSlab", "RIB-05",
        "IfcSlab har Pset_SlabCommon.LoadBearing",
        lambda el: _pset(el, "Pset_SlabCommon", "LoadBearing") is not None))
    d.rules.append(_check_elements(model, "IfcSlab", "RIB-06",
        "IfcSlab har material-assosiasjon", _has_material))

    # IfcWall: LoadBearing + IsExternal
    d.rules.append(_check_elements(model, "IfcWall", "RIB-07",
        "IfcWall har Pset_WallCommon.LoadBearing",
        lambda el: _pset(el, "Pset_WallCommon", "LoadBearing") is not None))
    d.rules.append(_check_elements(model, "IfcWall", "RIB-08",
        "IfcWall har Pset_WallCommon.IsExternal",
        lambda el: _pset(el, "Pset_WallCommon", "IsExternal") is not None))

    return d


def _validate_riv(model) -> DisciplineResult:
    """RIV – VVS (varme, ventilasjon, sanitær)."""
    d = DisciplineResult(discipline="RIV", label="VVS")

    d.rules.append(_check_elements(model, "IfcFlowTerminal", "RIV-01",
        "IfcFlowTerminal har Name", _has_name))
    d.rules.append(_check_elements(model, "IfcAirTerminal", "RIV-02",
        "IfcAirTerminal har Name", _has_name))
    d.rules.append(_check_elements(model, "IfcBoiler", "RIV-03",
        "IfcBoiler har Name", _has_name))
    d.rules.append(_check_elements(model, "IfcPump", "RIV-04",
        "IfcPump har Name", _has_name))
    d.rules.append(_check_elements(model, "IfcUnitaryEquipment", "RIV-05",
        "IfcUnitaryEquipment har Name", _has_name))

    return d


def _validate_riva(model) -> DisciplineResult:
    """RIVA – VA (vann/avløp)."""
    d = DisciplineResult(discipline="RIVA", label="Vann/avløp")

    d.rules.append(_check_elements(model, "IfcSanitaryTerminal", "RIVA-01",
        "IfcSanitaryTerminal har Name", _has_name))
    d.rules.append(_check_elements(model, "IfcSanitaryTerminal", "RIVA-02",
        "IfcSanitaryTerminal har Pset_SanitaryTerminalTypeCommon",
        lambda el: _pset(el, "Pset_SanitaryTerminalTypeCommon", "SanitaryTerminalType") is not None))

    return d


def _validate_rie(model) -> DisciplineResult:
    """RIE – Elektro."""
    d = DisciplineResult(discipline="RIE", label="Elektro")

    d.rules.append(_check_elements(model, "IfcElectricAppliance", "RIE-01",
        "IfcElectricAppliance har Name", _has_name))
    d.rules.append(_check_elements(model, "IfcLightFixture", "RIE-02",
        "IfcLightFixture har Name", _has_name))
    d.rules.append(_check_elements(model, "IfcLightFixture", "RIE-03",
        "IfcLightFixture har Pset_LightFixtureTypeCommon",
        lambda el: _pset(el, "Pset_LightFixtureTypeCommon", "LightFixtureType") is not None))

    return d


def _validate_ribr(model) -> DisciplineResult:
    """RIBR – Brann."""
    d = DisciplineResult(discipline="RIBR", label="Brann")

    d.rules.append(_check_elements(model, "IfcFireSuppressionTerminal", "RIBR-01",
        "IfcFireSuppressionTerminal har Name", _has_name))
    d.rules.append(_check_elements(model, "IfcDoor", "RIBR-02",
        "IfcDoor har Pset_DoorCommon.FireRating",
        lambda el: bool(_pset(el, "Pset_DoorCommon", "FireRating"))))
    d.rules.append(_check_elements(model, "IfcWall", "RIBR-03",
        "IfcWall har Pset_WallCommon.FireRating",
        lambda el: bool(_pset(el, "Pset_WallCommon", "FireRating"))))

    return d


def _validate_rien(model) -> DisciplineResult:
    """RIEN – Energi."""
    d = DisciplineResult(discipline="RIEN", label="Energi")

    d.rules.append(_check_elements(model, "IfcBuilding", "RIEN-01",
        "IfcBuilding har Pset_BuildingCommon.GrossPlannedArea",
        lambda el: _pset(el, "Pset_BuildingCommon", "GrossPlannedArea") is not None))
    d.rules.append(_check_elements(model, "IfcWindow", "RIEN-02",
        "IfcWindow har Qto_WindowBaseQuantities.Area",
        lambda el: _qty(el, "Qto_WindowBaseQuantities", "Area") is not None))
    d.rules.append(_check_elements(model, "IfcRoof", "RIEN-03",
        "IfcRoof har Pset_RoofCommon.IsExternal",
        lambda el: _pset(el, "Pset_RoofCommon", "IsExternal") is not None))

    return d


def _validate_riaku(model) -> DisciplineResult:
    """RIAKU – Akustikk."""
    d = DisciplineResult(discipline="RIAKU", label="Akustikk")

    d.rules.append(_check_elements(model, "IfcSpace", "RIAKU-01",
        "IfcSpace har Pset_SpaceCommon.AcousticRating",
        lambda el: bool(_pset(el, "Pset_SpaceCommon", "AcousticRating"))))

    return d


def _validate_ris(model) -> DisciplineResult:
    """RIS – Sikkerhet."""
    d = DisciplineResult(discipline="RIS", label="Sikkerhet")

    d.rules.append(_check_elements(model, "IfcDoor", "RIS-01",
        "IfcDoor har Pset_DoorCommon.SecurityRating",
        lambda el: bool(_pset(el, "Pset_DoorCommon", "SecurityRating"))))

    return d


def _validate_lark(model) -> DisciplineResult:
    """LARK – Landskapsarkitekt."""
    d = DisciplineResult(discipline="LARK", label="Landskapsarkitekt")
    # Sjekker IfcSite-eksistens og navn
    d.rules.append(_check_elements(model, "IfcSite", "LARK-01",
        "IfcSite har Name", _has_name))
    return d


def _validate_iark(model) -> DisciplineResult:
    """IARK – Interiørarkitekt."""
    d = DisciplineResult(discipline="IARK", label="Interiørarkitekt")
    d.rules.append(_check_elements(model, "IfcFurnishingElement", "IARK-01",
        "IfcFurnishingElement har Name", _has_name))
    return d


# ─── Hoved-validator ──────────────────────────────────────────────────────────

_DISCIPLINE_VALIDATORS = [
    _validate_rim,    # RIM (BIM-koordinering) – alltid first
    _validate_ark,
    _validate_lark,
    _validate_iark,
    _validate_rib,
    _validate_riv,
    _validate_riva,
    _validate_rie,
    _validate_riaku,
    _validate_ribr,
    _validate_ris,
    _validate_rien,
]


def validate_simba(file_bytes: bytes, filename: str = "model.ifc") -> SIMBAValidationResult:
    """
    Validerer en IFC-fil mot SIMBA 2.1-kravene.
    Lazy import av ifcopenshell – kaster ImportError om ikke installert.
    """
    try:
        import ifcopenshell  # type: ignore
    except ImportError:
        raise ImportError("ifcopenshell er ikke installert. Kjør: pip install ifcopenshell")

    import tempfile, os

    with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        model = ifcopenshell.open(tmp_path)
    finally:
        os.unlink(tmp_path)

    schema = model.schema
    projects = model.by_type("IfcProject")
    project_name = getattr(projects[0], "Name", filename) if projects else filename

    warnings: list[str] = []
    if schema not in ("IFC4", "IFC4X3"):
        warnings.append(
            f"SIMBA 2.1 krever IFC 4 (4.0.2.1). Denne filen bruker {schema}. "
            "Noen krav kan ikke valideres korrekt."
        )

    disciplines: list[DisciplineResult] = []
    for validator in _DISCIPLINE_VALIDATORS:
        try:
            disc = validator(model)
            disciplines.append(disc)
        except Exception as exc:
            logger.warning("SIMBA validator feilet for %s: %s", validator.__name__, exc)

    logger.debug(
        "SIMBA validering ferdig: schema=%s project=%s disipliner=%d",
        schema, project_name, len(disciplines),
    )

    return SIMBAValidationResult(
        schema=schema,
        project_name=project_name,
        disciplines=disciplines,
        warnings=warnings,
    )
