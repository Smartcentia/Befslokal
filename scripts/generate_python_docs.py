#!/usr/bin/env python3
"""
Generate expanded Python script documentation into docs/python.md.

Features:
- Scans backend/scripts and scripts/ for .py files
- Extracts top-level docstrings for concise explanations
- Heuristically describes scripts without docstrings
- Detects "used" scripts referenced in *.md and *.sh files
- Appends new sections to docs/python.md without overwriting existing content

Run:
  python3 scripts/generate_python_docs.py
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
DOCS_MD = ROOT / "docs" / "python.md"


def list_py_files(dir_path: Path) -> List[Path]:
    if not dir_path.exists():
        return []
    files = []
    for p in sorted(dir_path.glob("*.py")):
        # Skip caches or obvious non-script helpers
        if p.name == "__init__.py":
            continue
        files.append(p)
    return files


def read_docstring(path: Path) -> Optional[str]:
    """Extract the first top-level triple-quoted docstring if present."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    # Look for a docstring near top of file
    # Match """...""" or '''...''' at the beginning
    doc_match = re.search(r"^\s*[\"\']{3}(.*?)[\"\']{3}", text, re.DOTALL | re.MULTILINE)
    if doc_match:
        doc = doc_match.group(1).strip()
        # Only keep first line paragraph (concise)
        first_line = doc.splitlines()[0].strip()
        return first_line if first_line else doc
    return None


def heuristic_explanation(name: str) -> str:
    base = name.replace("_", " ").replace(".py", "")
    lower = base.lower()
    if lower.startswith("audit "):
        return f"Revisjon/avdekking: {base}"
    if lower.startswith("check ") or lower.startswith("sjekk "):
        return f"Sjekk/kontroll: {base}"
    if lower.startswith("verify "):
        return f"Verifiserer dataintegritet: {base}"
    if lower.startswith("inspect "):
        return f"Inspiserer/viser detaljer: {base}"
    if lower.startswith("export "):
        return f"Eksporterer data/rapport: {base}"
    if lower.startswith("import "):
        return f"Importer/berik: {base}"
    if lower.startswith("update "):
        return f"Oppdaterer data: {base}"
    if lower.startswith("seed "):
        return f"Seeder/testdata: {base}"
    if "geocode" in lower:
        return f"Geokoder adresser/koordinater: {base}"
    if "cron" in lower:
        return f"Planlagte jobber (cron): {base}"
    if "openai" in lower or "ai" in lower:
        return f"KI/LLM-relatert verktøy: {base}"
    return f"Script: {base}"


def scan_used_script_references(paths: List[Path]) -> List[str]:
    """Scan markdown and shell files for 'python scripts/<name>.py' references."""
    used = set()
    patterns = [
        re.compile(r"python3?\s+scripts/([\w_\-]+\.py)", re.IGNORECASE),
        re.compile(r"docker\s+compose\s+exec\s+backend\s+python\s+scripts/([\w_\-]+\.py)", re.IGNORECASE),
    ]
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for pat in patterns:
            for m in pat.finditer(text):
                used.add(m.group(1))
    return sorted(used)


def categorize_script(path: Path, doc: Optional[str]) -> str:
    name = path.name.lower()
    text = (doc or "").lower()
    def has(*keys: str) -> bool:
        return any(k in name or k in text for k in keys)
    # Finance
    if has("financial", "budget", "cost", "rent", "contract", "csv", "expenses", "audit"):
        return "Finans"
    # HMS & Internkontroll
    if has("hms", "checklist", "checklists", "internal_control", "risk", "deviation", "activities", "calendar"):
        return "HMS"
    # PDF & Dokument
    if has("pdf", "docling", "langextract", "parse_pdf", "search_pdf"):
        return "PDF"
    # Bufdir & Barnevern/BUP
    if has("bufdir", "barnevern", "bup", "familievern"):
        return "Bufdir"
    # Proximity & Geocode/Map
    if has("proximity", "geocode", "map", "locations"):
        return "Proximity"
    return "Andre"


def extract_usage_and_env(path: Path, doc: Optional[str], text: Optional[str]) -> Tuple[List[str], List[str]]:
    usage: List[str] = []
    envs: List[str] = []
    src = (text or "")
    d = (doc or "")
    # Usage lines in docstring
    for line in d.splitlines():
        if re.search(r"(Kjør|Usage|Bruk|Run)\b", line, re.IGNORECASE) and ("python" in line or "docker" in line):
            usage.append(line.strip())
    # Fallback: code comments mentioning usage
    for line in src.splitlines()[:120]:
        if re.search(r"python\s+scripts/|python3\s+scripts/|docker\s+compose\s+exec\s+backend\s+python", line):
            usage.append(line.strip())
    # Env detection: in docstring
    for line in d.splitlines():
        if re.search(r"(Krever|Requires)\b", line):
            # collect uppercase tokens
            envs.extend(re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", line))
    # Env detection: code
    envs.extend(re.findall(r"os\.environ\.get\([\"\']([A-Z0-9_]+)[\"\']\)", src))
    # Detect settings.<ENV_NAME> and getattr(settings, "ENV_NAME")
    envs.extend(re.findall(r"settings\.([A-Z0-9_]+)", src))
    envs.extend(re.findall(r"getattr\(settings,\s*[\"\']([A-Z0-9_]+)[\"\']", src))
    # Detect common provider namespaces (e.g., MASKINPORTEN_*, BRREG_*)
    envs.extend(re.findall(r"\b(MASKINPORTEN[A-Z0-9_]*|BRREG[A-Z0-9_]*)\b", src))
    # Common envs via settings references
    if "OPENAI_API_KEY" in src or "openai" in src:
        envs.append("OPENAI_API_KEY")
    # Common optional OpenAI vars
    if "OPENAI_BASE_URL" in src:
        envs.append("OPENAI_BASE_URL")
    if re.search(r"model\s*=\s*getattr\(settings,\s*[\"\']OPENAI_MODEL[\"\']", src):
        envs.append("OPENAI_MODEL")
    if "PDF_DOCS" in src:
        envs.append("PDF_DOCS")
    if "DATABASE_URL" in src or "SessionLocal" in src:
        envs.append("DATABASE_URL")
    # Deduplicate
    envs = sorted(set(envs))
    # Trim overly long usage list
    usage = usage[:4]
    return usage, envs


def build_explanations() -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]], Dict[str, List[Tuple[str, str, List[str], List[str]]]]]:
    """Return (used_explanations, all_explanations, grouped_by_domain)."""
    backend_scripts = list_py_files(ROOT / "backend" / "scripts")
    root_scripts = list_py_files(ROOT / "scripts")
    all_scripts = backend_scripts + root_scripts

    # Map filename -> path
    by_name: Dict[str, Path] = {p.name: p for p in all_scripts}

    # Scan references in docs and shell files
    doc_paths: List[Path] = []
    for rel in ("docs", "dokumentasjon", "backend/docs"):
        p = ROOT / rel
        if not p.exists():
            continue
        for r, _, files in os.walk(p):
            for f in files:
                if f.endswith(".md"):
                    doc_paths.append(Path(r) / f)
    # Shell wrappers
    for r, _, files in os.walk(ROOT / "scripts"):
        for f in files:
            if f.endswith(".sh"):
                doc_paths.append(Path(r) / f)

    used_names = scan_used_script_references(doc_paths)

    # Build explanation tuples
    def describe(name: str, path: Path) -> Tuple[str, Optional[str], Optional[str]]:
        file_text = None
        try:
            file_text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            file_text = None
        doc = read_docstring(path)
        desc = doc or heuristic_explanation(name)
        return desc, doc, file_text

    used_expl: List[Tuple[str, str]] = []
    grouped: Dict[str, List[Tuple[str, str, List[str], List[str]]]] = {}
    for name in used_names:
        p = by_name.get(name)
        if not p:
            # Might be in backend/scripts but referenced without backend/
            # Try to find by matching suffix
            candidates = [bp for bp in backend_scripts if bp.name == name]
            p = candidates[0] if candidates else None
        if p:
            desc, doc, file_text = describe(p.name, p)
            usage, envs = extract_usage_and_env(p, doc, file_text)
            used_expl.append((str(p.relative_to(ROOT)), desc))
            domain = categorize_script(p, doc)
            grouped.setdefault(domain, []).append((str(p.relative_to(ROOT)), desc, usage, envs))

    all_expl: List[Tuple[str, str]] = []
    for p in all_scripts:
        desc, doc, file_text = describe(p.name, p)
        usage, envs = extract_usage_and_env(p, doc, file_text)
        all_expl.append((str(p.relative_to(ROOT)), desc))
        domain = categorize_script(p, doc)
        grouped.setdefault(domain, []).append((str(p.relative_to(ROOT)), desc, usage, envs))

    # Deduplicate while preserving order
    seen = set()
    used_expl = [(a, b) for a, b in used_expl if not (a in seen or seen.add(a))]
    seen.clear()
    all_expl = [(a, b) for a, b in all_expl if not (a in seen or seen.add(a))]

    # Deduplicate grouped entries per domain by path
    for domain, items in list(grouped.items()):
        seen_paths = set()
        dedup = []
        for rel, desc, usage, envs in items:
            if rel in seen_paths:
                continue
            seen_paths.add(rel)
            dedup.append((rel, desc, usage, envs))
        grouped[domain] = dedup

    return used_expl, all_expl, grouped


def append_sections(md_path: Path, used: List[Tuple[str, str]], all_scripts: List[Tuple[str, str]], grouped: Dict[str, List[Tuple[str, str, List[str], List[str]]]]) -> None:
    header_used = "## Brukte Skript (Oppdaget via dokumentasjon)"
    header_all = "## Alle Skript – Auto-genererte forklaringer"
    header_grouped = "## Domenegjennomgang (Finans, HMS, PDF, Bufdir, Proximity)"
    header_env = "## Miljøvariabler (referanse)"

    def fmt(items: List[Tuple[str, str]]) -> str:
        lines = []
        for rel, desc in items:
            # Markdown link to file with concise description
            lines.append(f"- [{rel}]({rel}): {desc}")
        return "\n".join(lines) + "\n"

    def fmt_grouped(groups: Dict[str, List[Tuple[str, str, List[str], List[str]]]]) -> str:
        order = ["Finans", "HMS", "PDF", "Bufdir", "Proximity", "Andre"]
        out = []
        for domain in order:
            items = groups.get(domain) or []
            if not items:
                continue
            out.append(f"### {domain}\n")
            for rel, desc, usage, envs in sorted(items, key=lambda t: t[0]):
                out.append(f"- [{rel}]({rel}): {desc}")
                if usage:
                    for u in usage:
                        out.append(f"  - Usage: {u}")
                if envs:
                    out.append(f"  - Env: {', '.join(sorted(set(envs)))}")
            out.append("")
        return "\n".join(out)

    def fmt_env_reference(groups: Dict[str, List[Tuple[str, str, List[str], List[str]]]]) -> str:
        # Aggregate envs across all items
        env_set = set()
        for items in groups.values():
            for _, _, _, envs in items:
                for e in envs:
                    env_set.add(e)
        # Known descriptions
        descriptions = {
            "DATABASE_URL": "Postgres connection string used by backend scripts.",
            "OPENAI_API_KEY": "API key for OpenAI LLM integrations.",
            "OPENAI_BASE_URL": "Optional override for OpenAI HTTP endpoint.",
            "OPENAI_MODEL": "Model name used when calling OpenAI (e.g., gpt-4o-mini).",
            "PDF_DOCS": "Path to folder containing PDF documents to process.",
        }
        # Pattern-based notes
        has_maskinporten = any(e.startswith("MASKINPORTEN") for e in env_set)
        has_brreg = any(e.startswith("BRREG") for e in env_set)

        lines = []
        for var in sorted(env_set):
            desc = descriptions.get(var, "(se settings)")
            lines.append(f"- `{var}`: {desc}")
        if has_maskinporten:
            lines.append("- `MASKINPORTEN_*`: Credentials/config for Maskinporten integrations.")
        if has_brreg:
            lines.append("- `BRREG_*`: Configuration for BRREG service access.")
        return "\n".join(lines) + "\n"

    try:
        existing = md_path.read_text(encoding="utf-8", errors="replace") if md_path.exists() else ""

        def replace_or_insert(content: str, header: str, body: str, anchor_header: Optional[str] = None, after: bool = True) -> str:
            # Replace section starting at header until next '## ' or end; else insert near anchor_header
            pattern = re.compile(rf"(^\s*{re.escape(header)}\s*$)(.*?)(?=^\s*##\s|\Z)", re.MULTILINE | re.DOTALL)
            if pattern.search(content):
                content = pattern.sub(f"{header}\n\n{body}", content)
            else:
                if anchor_header:
                    anchor_pat = re.compile(rf"^\s*{re.escape(anchor_header)}\s*$", re.MULTILINE)
                    m = anchor_pat.search(content)
                    if m:
                        insert_pos = m.end()
                        if after:
                            content = content[:insert_pos] + "\n\n" + f"{header}\n\n{body}" + content[insert_pos:]
                        else:
                            content = content[:m.start()] + f"{header}\n\n{body}\n\n" + content[m.start():]
                    else:
                        content = content.rstrip() + "\n\n" + f"{header}\n\n{body}"
                else:
                    content = content.rstrip() + "\n\n" + f"{header}\n\n{body}"
            return content

        grouped_body = fmt_grouped(grouped)
        used_body = (fmt(used) if used else "(Ingen referanser funnet)\n")
        all_body = fmt(all_scripts)
        env_body = fmt_env_reference(grouped)

        # Insert/replace grouped section right after Safe Scripts
        updated = replace_or_insert(existing, header_env, env_body, anchor_header="## Safe Scripts (Analyst)")
        updated = replace_or_insert(updated, header_grouped, grouped_body, anchor_header=header_env)
        # Insert/replace used section after grouped
        updated = replace_or_insert(updated, header_used, used_body, anchor_header=header_grouped)
        # Replace or append full auto-generated index at end
        updated = replace_or_insert(updated, header_all, all_body)

        md_path.write_text(updated, encoding="utf-8")
        print(f"Updated {md_path} with {len(used)} used, {len(all_scripts)} total, grouped in {len(grouped)} domains.")
    except Exception as e:
        print(f"Failed to update {md_path}: {e}")


def main():
    used_expl, all_expl, grouped = build_explanations()
    append_sections(DOCS_MD, used_expl, all_expl, grouped)


if __name__ == "__main__":
    main()
