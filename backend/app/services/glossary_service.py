import json
import os
from pathlib import Path
from typing import List, Dict, Any

# Alltid backend-roten (…/backend), uavhengig av monorepo vs. Railway (/app).
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
GLOSSARY_FILE = _BACKEND_ROOT / "data" / "glossary_terms.json"
OUTPUT_FILE = _BACKEND_ROOT / "data" / "term_usage_report.json"

# Monorepo-rot når frontend finnes ved siden av backend (lokal utvikling)
_REPO_ROOT = _BACKEND_ROOT.parent
_IS_MONOREPO = (_REPO_ROOT / "frontend").is_dir() and _REPO_ROOT.name != "frontend"

# Extensions to scan
EXTENSIONS = {".py", ".md", ".tsx", ".ts", ".js", ".jsx"}


def _scan_dir_paths() -> List[Path]:
    """Mapper som finnes: backend/app, backend/docs, og ev. frontend/* i monorepo."""
    roots: List[Path] = []
    for sub in ("app", "docs"):
        p = _BACKEND_ROOT / sub
        if p.is_dir():
            roots.append(p)
    if _IS_MONOREPO:
        for sub in ("components", "lib", "app"):
            p = _REPO_ROOT / "frontend" / sub
            if p.is_dir():
                roots.append(p)
    return roots


def _relative_report_path(file_path: Path) -> str:
    fp = file_path.resolve()
    if _IS_MONOREPO:
        try:
            return str(fp.relative_to(_REPO_ROOT.resolve()))
        except ValueError:
            pass
    try:
        return str(fp.relative_to(_BACKEND_ROOT.resolve()))
    except ValueError:
        return str(fp)


def load_terms() -> List[Dict[str, Any]]:
    if not GLOSSARY_FILE.exists():
        print(f"Error: {GLOSSARY_FILE} not found.")
        return []
    try:
        with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading terms: {e}")
        return []


def scan_file(file_path: Path, terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    found_matches = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        content_lower = content.lower()

        for term_obj in terms:
            term = term_obj["term"]
            term_lower = term.lower()

            if term_lower in content_lower:
                for i, line in enumerate(content.splitlines()):
                    if term_lower in line.lower():
                        found_matches.append({
                            "term": term,
                            "file": _relative_report_path(file_path),
                            "line": i + 1,
                            "context": line.strip()[:100]
                        })
    except Exception as e:
        print(f"Error scanning {file_path}: {e}")

    return found_matches


def run_glossary_scan() -> Dict[str, Any]:
    print("Starting Glossary Scan...")
    terms = load_terms()
    print(f"Loaded {len(terms)} terms.")

    all_matches = []
    scan_roots = _scan_dir_paths()
    if not scan_roots:
        return {
            "status": "error",
            "error": "Ingen kataloger å skanne (forventet minst backend/app).",
        }

    for scan_path in scan_roots:
        for root, dirs, files in os.walk(scan_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in EXTENSIONS:
                    matches = scan_file(file_path, terms)
                    all_matches.extend(matches)

    print(f"Found {len(all_matches)} matches.")

    try:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_matches, f, indent=2, ensure_ascii=False)
        print(f"Saved usage report to {OUTPUT_FILE}")
        return {
            "status": "success",
            "terms_count": len(terms),
            "matches_count": len(all_matches),
            "output_file": str(OUTPUT_FILE),
            "matches": all_matches
        }
    except Exception as e:
        print(f"Error saving report: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
