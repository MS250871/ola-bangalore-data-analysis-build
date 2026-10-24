"""Shared helpers for the Data Analysis Build kit scripts.

Every script finds the project root by walking up from the current folder (or --root) until it
finds PROJECT_RULES.md. Settings live in "02 Setup and Log/project.json".
Works with pandas 2.x and 3.x and openpyxl 3.1+. No other third-party packages."""
import os, sys, json, hashlib, datetime, re

FOLDERS = ["Raw Data", "01 Framing", "02 Setup and Log", "03 Data Inspection", "04 Quality Audit",
           "05 Cleaning and Prep", "06 Question Bank", "07 Analysis", "08 Excel Dashboard",
           "09 Web Dashboard", "10 Dash Handoff"]
LOG_REL = os.path.join("02 Setup and Log", "Analysis Log.md")
CFG_REL = os.path.join("02 Setup and Log", "project.json")
LOG_HEADER = ("| Date | Step | Tool Used | Prompt | Output | Human Check | Decision |\n"
              "|------|------|-----------|--------|--------|-------------|----------|\n")


def find_root(start=None):
    p = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.exists(os.path.join(p, "PROJECT_RULES.md")):
            return p
        parent = os.path.dirname(p)
        if parent == p:
            sys.exit("ERROR: PROJECT_RULES.md not found. Run from inside the project folder or pass --root.")
        p = parent


def load_cfg(root):
    f = os.path.join(root, CFG_REL)
    if not os.path.exists(f):
        return {}
    with open(f, encoding="utf-8") as fh:
        return json.load(fh)


def save_cfg(root, cfg):
    f = os.path.join(root, CFG_REL)
    tmp = f + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, f)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def today():
    return datetime.date.today().isoformat()


def cell(s):
    """Make text safe for one log cell: no pipes, no raw newlines."""
    s = "" if s is None else str(s)
    s = s.replace("|", "/").replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"\n+", "<br>", s.strip())
    return s


def read_tables(path, sheets=None):
    """Return {table_name: DataFrame} for a .csv/.tsv/.xlsx/.xlsm/.xls file."""
    import pandas as pd
    ext = os.path.splitext(path)[1].lower()
    name = os.path.splitext(os.path.basename(path))[0]
    if ext in (".csv", ".txt"):
        return {name: pd.read_csv(path, low_memory=False)}
    if ext == ".tsv":
        return {name: pd.read_csv(path, sep="\t", low_memory=False)}
    if ext in (".xlsx", ".xlsm", ".xls"):
        d = pd.read_excel(path, sheet_name=sheets if sheets else None)
        return d if isinstance(d, dict) else {sheets: d}
    if ext == ".parquet":
        return {name: pd.read_parquet(path)}
    if ext == ".json":
        return {name: pd.read_json(path)}
    raise SystemExit(f"Unsupported file type: {path}")


def raw_files(root):
    rd = os.path.join(root, "Raw Data")
    out = []
    for dp, _, fs in os.walk(rd):
        for f in sorted(fs):
            if f.startswith("~$") or f.startswith("."):
                continue
            out.append(os.path.join(dp, f))
    return out


def write_json(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, default=_default)


def _default(o):
    try:
        import numpy as np
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return None if o != o else float(o)
        if isinstance(o, np.bool_):
            return bool(o)
    except ImportError:
        pass
    if hasattr(o, "isoformat"):
        return o.isoformat()
    return str(o)
