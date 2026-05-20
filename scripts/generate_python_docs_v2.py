import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIRS = [ROOT / "backend" / "scripts", ROOT / "scripts"]
OUTPUT_MD = ROOT / "docs" / "python.md"

ENV_REGEXES = [
    re.compile(r"os\.getenv\(['\"]([A-Z0-9_]+)['\"]"),
    re.compile(r"os\.environ\[['\"]([A-Z0-9_]+)['\"]\]"),
]
SQL_WRITE_HINTS = [r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bALTER\b", r"\bDROP\b", r"\bCREATE\b"]
ORM_WRITE_HINTS = [r"\bsession\.add\b", r"\bsession\.commit\b", r"\bsession\.merge\b", r"\bsession\.delete\b"]
FILE_WRITE_HINTS = [r"\bopen\([^,]+,\s*['\"]w['\"]", r"\bopen\([^,]+,\s*['\"]a['\"]", r"\bPath\(.+\)\.write_text\b", r"\bPath\(.+\)\.write_bytes\b"]

EXTERNAL_HINTS = [
    ("OpenAI", re.compile(r"\bopenai\b|\bOPENAI_API_KEY\b", re.I)),
    ("Maskinporten", re.compile(r"\bmaskinporten\b|\bRRH_MASKINPORTEN\b", re.I)),
    ("BRREG", re.compile(r"\bbrreg\b", re.I)),
    ("HTTP/requests", re.compile(r"\brequests\b", re.I)),
    ("LangExtract", re.compile(r"\blangextract\b", re.I)),
    ("Docling/PDF", re.compile(r"\bdocling\b|\bpdf\b", re.I)),
    ("Kartverket/Geonorge", re.compile(r"\bkartverket\b|\bgeonorge\b", re.I)),
    ("NVE", re.compile(r"\bnve\b", re.I)),
    ("Postgres/SQL", re.compile(r"\bpsycopg2\b|\bsqlalchemy\b|\bSELECT\b", re.I)),
]

CATEGORY_RULES = [
    ("Finans", re.compile(r"\bfinancial|manual_expenses|rent|gl_transactions|budget\b", re.I)),
    ("HMS", re.compile(r"\bhms|internkontroll|risk|checklist\b", re.I)),
    ("PDF", re.compile(r"\bpdf|docling|ocr|parse\b", re.I)),
    ("Bufdir", re.compile(r"\bbufdir|barnevern\b", re.I)),
    ("Proximity", re.compile(r"\bgeocode|coords|proximity\b", re.I)),
]

# Security heuristics
RX_SQL_EXECUTE_FSTR = re.compile(r"\bexecute\(\s*f['\"]", re.I)
RX_SQL_EXECUTE_FORMAT = re.compile(r"\bexecute\(\s*['\"].+?['\"]\.format\(", re.I | re.S)
RX_SQL_TEXT_FSTR = re.compile(r"\btext\(\s*f['\"]", re.I)
RX_SUBPROCESS_SHELL = re.compile(r"\bsubprocess\.(Popen|call|run)\(.*shell\s*=\s*True", re.I | re.S)
RX_OS_SYSTEM = re.compile(r"\bos\.system\(", re.I)
RX_EVAL_EXEC = re.compile(r"\b(eval|exec)\(", re.I)
RX_REQUESTS_NO_TIMEOUT = re.compile(r"requests\.(get|post|put|delete|patch)\([^)]*(?!timeout=)[^)]*\)", re.I)
RX_REQUESTS_VERIFY_FALSE = re.compile(r"requests\.(get|post|put|delete|patch)\([^)]*verify\s*=\s*False", re.I)
RX_YAML_UNSAFE = re.compile(r"yaml\.load\(", re.I)
RX_PICKLE_LOAD = re.compile(r"pickle\.load\(", re.I)
RX_BROAD_EXCEPT = re.compile(r"except\s*(Exception)?\s*:\s*", re.I)
RX_HARDCODED_OPENAI = re.compile(r"sk-[A-Za-z0-9]{20,}", re.I)
RX_HARDCODED_AWS = re.compile(r"AKIA[0-9A-Z]{16}", re.I)
RX_PRIVKEY = re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH|PRIVATE) KEY-----", re.I)
RX_URL_FROM_ARGV = re.compile(r"(sys\.argv\[|argparse\.)", re.I)
RX_OPEN_FROM_ARGV = re.compile(r"open\([^)]*sys\.argv", re.I)
RX_DISABLE_WARNINGS = re.compile(r"urllib3\.disable_warnings", re.I)

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def extract_docstring(src: str) -> Optional[str]:
    try:
        tree = ast.parse(src)
        doc = ast.get_docstring(tree)
        return doc
    except Exception:
        return None

def extract_top_comments(src: str) -> List[str]:
    lines = src.splitlines()
    comments = []
    for line in lines:
        if line.strip().startswith("#"):
            comments.append(line.strip().lstrip("#").strip())
        elif line.strip() and not line.strip().startswith("#"):
            break
    return comments

def extract_env_vars(src: str) -> List[str]:
    envs = set()
    for rx in ENV_REGEXES:
        for m in rx.findall(src):
            envs.add(m)
    for m in re.findall(r"\b([A-Z][A-Z0-9_]{2,})\b", src):
        if m in {"True","False"}:
            continue
        if m.endswith("_PATH") or m.endswith("_URL") or m.startswith("OPENAI") or m.startswith("POSTGRES") or m.startswith("DATABASE"):
            envs.add(m)
    return sorted(envs)

def has_write_ops(src: str) -> bool:
    for rx in SQL_WRITE_HINTS + ORM_WRITE_HINTS + FILE_WRITE_HINTS:
        if re.search(rx, src):
            return True
    return False

def detect_external(src: str) -> List[str]:
    hits = []
    for name, rx in EXTERNAL_HINTS:
        if rx.search(src):
            hits.append(name)
    return hits

def extract_usage_strings(src: str) -> List[str]:
    usages = []
    for line in src.splitlines():
        if re.search(r"\bUsage\b|Bruk:", line, re.I):
            usages.append(line.strip())
    arg_lines = []
    for line in src.splitlines():
        if "add_argument(" in line:
            arg_lines.append(line.strip())
    if arg_lines:
        usages.append("Args: " + "; ".join(arg_lines))
    return usages

def categorize(name: str, src: str) -> str:
    for cat, rx in CATEGORY_RULES:
        if rx.search(src) or rx.search(name):
            return cat
    return "Andre"

def describe_from_name(name: str) -> str:
    cleaned = name.replace("_", " ").replace(".py", "")
    return f"{cleaned.capitalize()}."

def detect_risks(src: str) -> Tuple[str, List[str], List[str]]:
    findings: List[str] = []
    fixes: List[str] = []

    if RX_SQL_EXECUTE_FSTR.search(src) or RX_SQL_EXECUTE_FORMAT.search(src) or RX_SQL_TEXT_FSTR.search(src):
        findings.append("Potensiell SQL-injection (f-string/format i execute/text).")
        fixes.append("Bruk parameterisering (psycopg2 %s/params eller SQLAlchemy bindparam).")

    if RX_SUBPROCESS_SHELL.search(src) or RX_OS_SYSTEM.search(src):
        findings.append("Usikker subprocess (shell=True) eller os.system.")
        fixes.append("Unngå shell=True; bruk liste-args og sjekk input.")
    if RX_EVAL_EXEC.search(src):
        findings.append("Bruk av eval/exec.")
        fixes.append("Fjern eval/exec; bruk trygge parser/mapper.")

    if RX_REQUESTS_NO_TIMEOUT.search(src):
        findings.append("HTTP-kall uten timeout.")
        fixes.append("Legg til timeout=30 (eller passende).")
    if RX_REQUESTS_VERIFY_FALSE.search(src) or RX_DISABLE_WARNINGS.search(src):
        findings.append("TLS verifisering deaktivert (verify=False) eller advarsler slått av.")
        fixes.append("Aktiver TLS verifisering; bruk sertifikat-pinning ved behov.")

    if RX_YAML_UNSAFE.search(src):
        findings.append("yaml.load uten SafeLoader.")
        fixes.append("Bruk yaml.safe_load.")
    if RX_PICKLE_LOAD.search(src):
        findings.append("pickle.load kan deserialisere utrygt innhold.")
        fixes.append("Bruk JSON/MessagePack; hvis nødvendig, valider kilde og signer data.")

    if RX_BROAD_EXCEPT.search(src):
        findings.append("Bred unntaksfanging (except/except Exception).")
        fixes.append("Fang spesifikke unntak; logg og håndter eksplisitt.")

    if RX_HARDCODED_OPENAI.search(src) or RX_HARDCODED_AWS.search(src) or RX_PRIVKEY.search(src):
        findings.append("Hardkodede hemmeligheter/nøkler oppdaget.")
        fixes.append("Flytt til miljøvariabler/secret manager og roter nøklene.")

    if RX_URL_FROM_ARGV.search(src) and "requests." in src:
        findings.append("URL kan komme fra argv/brukerinput (SSRF-risiko).")
        fixes.append("Valider/whitelist domener; blokker interne IP-intervaller.")
    if RX_OPEN_FROM_ARGV.search(src):
        findings.append("Filsti fra argv (mulig path traversal).")
        fixes.append("Normaliser og begrens til sikkert rot; bruk allowlist.")

    if has_write_ops(src):
        findings.append("Skript utfører skrivende operasjoner (DB/fil).")
        fixes.append("Kjør med --dry-run og transaksjoner; audit-logger endringer.")

    high_markers = ["SQL-injection", "Usikker subprocess", "eval/exec", "TLS verifisering deaktivert", "yaml.load", "pickle.load", "hardkodede"]
    high = any(any(hm in f for hm in high_markers) for f in findings)
    medium = (not high) and (len(findings) > 0)
    risk = "Høy" if high else ("Middels" if medium else "Lav")

    return risk, findings, fixes

def analyze_script(path: Path) -> Dict:
    src = read_text(path)
    doc = extract_docstring(src)
    comments = extract_top_comments(src)
    envs = extract_env_vars(src)
    usage = extract_usage_strings(src)
    external = detect_external(src)
    category = categorize(path.name, src)
    safety = "Safe (lese/analyse)" if not has_write_ops(src) else "Endrer data (skriv/sideeffekter)"
    description = doc or (comments[0] if comments else describe_from_name(path.name))
    risk, findings, fixes = detect_risks(src)
    return {
        "path": str(path.relative_to(ROOT)),
        "name": path.name,
        "category": category,
        "description": description,
        "envs": envs,
        "usage": usage,
        "external": external,
        "safety": safety,
        "risk": risk,
        "findings": findings,
        "fixes": fixes,
    }

def gather_scripts() -> List[Path]:
    files = []
    for d in SCRIPT_DIRS:
        if not d.exists():
            continue
        files.extend(sorted(d.rglob("*.py")))
    files = [p for p in files if p.name != Path(__file__).name]
    return files

def render_header() -> str:
    return (
        "# Python Scripts – Utvidet dokumentasjon og sårbarhetsvurdering\n\n"
        "Denne siden er auto-generert. Den beskriver hvert skript og inkluderer en heuristisk vurdering av sårbarheter/svakheter.\n"
        "NB: Heuristikken er konservativ og kan gi falske positiver; bruk som sjekkliste ved kodegjennomgang.\n\n"
        "---\n\n"
    )

def render_script_entry(info: Dict) -> str:
    envs = ", ".join(info["envs"]) if info["envs"] else "Ingen spesifikke"
    extern = ", ".join(info["external"]) if info["external"] else "Ingen"
    usage_md = ""
    if info["usage"]:
        usage_md = "\n".join(f"- {u}" for u in info["usage"])
    findings_md = "\n".join(f"- {f}" for f in info["findings"]) if info["findings"] else "- Ingen evidente risikofunn (heuristisk)."
    fixes_md = "\n".join(f"- {f}" for f in info["fixes"]) if info["fixes"] else "- Ingen."
    return (
        f"## {info['name']}\n"
        f"- Kategori: {info['category']}\n"
        f"- Fil: {info['path']}\n"
        f"- Sikkerhet: {info['safety']}\n"
        f"- Miljøvariabler: {envs}\n"
        f"- Eksterne tjenester: {extern}\n"
        f"- Risiko (heuristisk): {info['risk']}\n\n"
        f"### Beskrivelse\n{info['description']}\n\n"
        f"### Bruk\n{usage_md or '- (ingen eksplisitt usage funnet)'}\n\n"
        f"### Sårbarheter og svakheter\n{findings_md}\n\n"
        f"### Foreslåtte tiltak\n{fixes_md}\n\n"
        "---\n\n"
    )

def build_markdown(infos: List[Dict]) -> str:
    by_cat: Dict[str, List[Dict]] = {}
    for i in infos:
        by_cat.setdefault(i["category"], []).append(i)
    for k in by_cat:
        by_cat[k].sort(key=lambda x: x["name"].lower())

    md = [render_header()]
    high_risk = [i for i in infos if i["risk"] == "Høy"]
    if high_risk:
        md.append("## Høyrisiko skript (heuristisk)\n\n")
        for i in high_risk:
            md.append(f"- {i['name']} ({i['path']})\n")
        md.append("\n---\n\n")

    for cat in sorted(by_cat.keys()):
        md.append(f"# {cat}\n\n")
        for info in by_cat[cat]:
            md.append(render_script_entry(info))
    return "".join(md)

def main(out_path: Optional[Path] = None):
    infos = [analyze_script(p) for p in gather_scripts()]
    md = build_markdown(infos)
    target = out_path or OUTPUT_MD
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(md, encoding="utf-8")
    print(f"Wrote: {target}")

if __name__ == "__main__":
    custom = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
    main(custom)
