"""File Integrity Check (PROJECT_RULES.md). Reopens saved files from disk and reports PASS/FAIL per check.

Usage:
  python integrity_check.py FILE [FILE...] [--sheets "Index,Q01_KPIs,Orders"] [--rows "Orders=51290,Returns=1079"]
                            [--min-pivots 13] [--min-slicers 4] [--expect "07 Analysis/expected_values.json"]
                            [--recalc]   (LibreOffice headless recalculation, if installed, to compare values)
                            [--totals "Orders:Sales=12642501.91,Profit=1467457.29"]

.xlsx : opens with openpyxl; sheet names (and order if --sheets given); data rows per sheet; Excel Tables;
        formula error values in cached cells; package parts: PivotTables, pivot caches, slicers, slicer caches,
        charts, drawings; every PivotTable points to an existing cache; every slicer cache lists PivotTables
        that exist; with --recalc, a LibreOffice copy is recalculated and dashboard/v3 values are compared
        with expected_values.json (PivotTables themselves refresh only in Excel; that part stays a human check).
.csv  : parses; row count; optional --totals.
.json : parses; top-level type and size.
.html : file size; no external <script src>/<link href> to other hosts; data inlined (if no data/ folder).
Exit code 1 if any check fails. Always lists what could NOT be checked."""
import os, sys, re, json, zipfile, argparse, subprocess, tempfile, shutil, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ap = argparse.ArgumentParser()
ap.add_argument("files", nargs="+")
ap.add_argument("--sheets")
ap.add_argument("--rows")
ap.add_argument("--min-pivots", type=int)
ap.add_argument("--min-slicers", type=int)
ap.add_argument("--expect")
ap.add_argument("--recalc", action="store_true")
ap.add_argument("--totals", action="append", default=[])
A = ap.parse_args()
RES, NOT = [], []
ERRS = ("#REF!", "#N/A", "#DIV/0!", "#VALUE!", "#NAME?", "#NUM!", "#NULL!")


def chk(ok, what, detail=""):
    RES.append(("PASS" if ok else "FAIL", what, detail))


def parse_totals():
    out = {}
    for t in A.totals:
        tbl, rest = t.split(":", 1)
        out[tbl] = {k: float(v) for k, v in (x.split("=") for x in rest.split(","))}
    return out


def check_xlsx(f):
    from openpyxl import load_workbook
    try:
        z = zipfile.ZipFile(f); names = z.namelist(); bad = z.testzip()
        chk(bad is None, f"{f}: zip package valid", bad or "")
    except Exception as e:
        chk(False, f"{f}: opens as a zip package", str(e)); return
    try:
        wb = load_workbook(f, read_only=False, data_only=True)
    except Exception as e:
        chk(False, f"{f}: opens with openpyxl", str(e)); return
    sheets = wb.sheetnames
    chk(True, f"{f}: opens with openpyxl", f"{len(sheets)} sheets: {', '.join(sheets)}")
    if A.sheets:
        exp = [s.strip() for s in A.sheets.split(",")]
        chk(sheets == exp, f"{f}: sheet names and order match the expected list",
            "" if sheets == exp else f"expected {exp} got {sheets}")
    rows = dict(x.split("=") for x in A.rows.split(",")) if A.rows else {}
    errs = []
    for ws in wb.worksheets:
        if ws.title in rows:
            n = ws.max_row - 1
            chk(n == int(rows[ws.title]), f"{f}: '{ws.title}' data rows = {rows[ws.title]}", f"found {n}")
        if ws.max_row * ws.max_column <= 2_000_000:
            for row in ws.iter_rows():
                for c in row:
                    if isinstance(c.value, str) and c.value.strip() in ERRS:
                        errs.append(f"{ws.title}!{c.coordinate}={c.value}")
    chk(not errs, f"{f}: no formula error values in saved cells", ", ".join(errs[:10]))
    tables = {ws.title: list(ws.tables.keys()) for ws in wb.worksheets if ws.tables}
    RES.append(("INFO", f"{f}: Excel Tables", json.dumps(tables)))
    piv = [n for n in names if re.match(r"xl/pivotTables/pivotTable\d+\.xml$", n)]
    caches = [n for n in names if re.match(r"xl/pivotCache/pivotCacheDefinition\d+\.xml$", n)]
    slc = [n for n in names if re.match(r"xl/slicers/slicer\d*[^/]*\.xml$", n)]
    slc_objs = sum(len(re.findall(r"<slicer ", z.read(n).decode("utf-8", "ignore"))) for n in slc)
    scache = [n for n in names if re.match(r"xl/slicerCaches/slicerCache\d+\.xml$", n)]
    charts = [n for n in names if re.match(r"xl/charts/chart\d+\.xml$", n)]
    RES.append(("INFO", f"{f}: parts", f"PivotTables={len(piv)} pivot caches={len(caches)} slicers={slc_objs} slicer caches={len(scache)} charts={len(charts)}"))
    if A.min_pivots is not None:
        chk(len(piv) >= A.min_pivots, f"{f}: PivotTables >= {A.min_pivots}", f"found {len(piv)}")
    if A.min_slicers is not None:
        chk(slc_objs >= A.min_slicers, f"{f}: slicers >= {A.min_slicers}", f"found {slc_objs}")
    wbx = z.read("xl/workbook.xml").decode()
    cache_ids = set(re.findall(r'<pivotCache cacheId="(\d+)"', wbx))
    pt_names, broken = [], []
    for n in piv:
        x = z.read(n).decode()
        pt_names.append(re.search(r' name="([^"]+)"', x).group(1))
        cid = re.search(r'cacheId="(\d+)"', x).group(1)
        if cid not in cache_ids:
            broken.append(n)
        loc = re.search(r'<location ref="([A-Z]+\d+)', x)
    if piv:
        chk(not broken, f"{f}: every PivotTable points to a registered pivot cache", ", ".join(broken))
        # overlapping anchors on the same sheet are a classic cause of Excel repair prompts
    for n in scache:
        x = z.read(n).decode()
        missing = [p for p in re.findall(r'<pivotTable tabId="\d+" name="([^"]+)"', x) if p not in pt_names]
        chk(not missing, f"{f}: {os.path.basename(n)} links only to existing PivotTables", ", ".join(missing))
    if A.expect and A.recalc:
        recalc_compare(f)
    elif A.expect:
        NOT.append(f"{f}: values not recomputed (run with --recalc where LibreOffice is installed)")
    NOT.append(f"{f}: opening in desktop Excel (repair prompt or not) and clicking slicers: ask the user")


def recalc_compare(f):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        NOT.append(f"{f}: LibreOffice not installed, so no recalculation check"); return
    from openpyxl import load_workbook
    tmpd = tempfile.mkdtemp()
    try:
        subprocess.run([soffice, "--headless", "--calc", "--convert-to", "xlsx", "--outdir", tmpd, f],
                       capture_output=True, timeout=300)
        outs = glob.glob(os.path.join(tmpd, "*.xlsx"))
        if not outs:
            NOT.append(f"{f}: LibreOffice conversion failed"); return
        wb = load_workbook(outs[0], data_only=True)
        E = json.load(open(A.expect, encoding="utf-8"))
        # compare cells that the builder linked: Dashboard mirrors are labelled; we compare grand totals found in Q sheets
        compared = mism = 0
        detail, skipped = [], []
        for name, pv in ([] if E.get("cell_checks") else E["pivots"].items()):
            sh = pv["sheet"]
            if sh not in wb.sheetnames:
                continue
            ws = wb[sh]
            vals = [c.value for row in ws.iter_rows() for c in row if isinstance(c.value, (int, float))]
            for cap, v in pv["grand_total"].items():
                if v is None:
                    continue
                if cap in pv.get("calc_captions", []):
                    skipped.append(f"{name} {cap}"); continue
                compared += 1
                if not any(abs(x - v) <= max(0.01, abs(v) * 1e-6) for x in vals):
                    mism += 1; detail.append(f"{name} {cap} expected {v}")
        cc = E.get("cell_checks", [])
        if cc:
            n_ok, n_bad, n_skip, bad = 0, 0, 0, []
            calc_lo = E.get("mode") in ("v1", "v2")
            for c in cc:
                if c["sheet"] not in wb.sheetnames:
                    continue
                if c["calc"] and calc_lo:
                    n_skip += 1; continue
                got = wb[c["sheet"]][c["cell"]].value
                exp_v = c["expected"]
                ok = isinstance(got, (int, float)) and abs(got - exp_v) <= max(0.005, abs(exp_v) * 1e-6)
                if ok: n_ok += 1
                else:
                    n_bad += 1; bad.append(f"{c['sheet']}!{c['cell']} {c['key']} expected {exp_v:.6g} got {got}")
            chk(n_bad == 0, f"{f}: after LibreOffice recalculation, {n_ok + n_bad} formula cells match pandas", "; ".join(bad[:6]))
            if n_skip:
                NOT.append(f"{f}: {n_skip} formula cells that read PivotTable calculated fields (LibreOffice cannot evaluate them): check in desktop Excel")
        if skipped:
            NOT.append(f"{f}: calculated-field values ({len(skipped)}: {', '.join(skipped[:6])}...) because LibreOffice does not evaluate PivotTable calculated fields; check them in desktop Excel against expected_values.json")
        if compared:
            chk(mism == 0, f"{f}: after LibreOffice recalculation, {compared} grand totals found on their sheets", "; ".join(detail[:6]))
        else:
            NOT.append(f"{f}: no grand totals to compare after recalculation")
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)


def check_csv(f):
    import pandas as pd
    try:
        df = pd.read_csv(f, low_memory=False)
    except Exception as e:
        chk(False, f"{f}: parses as CSV", str(e)); return
    chk(True, f"{f}: parses as CSV", f"{len(df):,} rows x {len(df.columns)} columns")
    stem = os.path.basename(f).replace("_final.csv", "").replace(".csv", "")
    rows = dict(x.split("=") for x in A.rows.split(",")) if A.rows else {}
    if stem in rows:
        chk(len(df) == int(rows[stem]), f"{f}: rows = {rows[stem]}", f"found {len(df)}")
    for col, v in parse_totals().get(stem, {}).items():
        got = float(pd.to_numeric(df[col], errors="coerce").sum())
        chk(abs(got - v) < 0.01, f"{f}: total {col} = {v}", f"found {got:.2f}")


def check_json(f):
    try:
        d = json.load(open(f, encoding="utf-8"))
        chk(True, f"{f}: parses as JSON", f"{type(d).__name__}, {len(d) if hasattr(d, '__len__') else ''} items, {os.path.getsize(f):,} bytes")
    except Exception as e:
        chk(False, f"{f}: parses as JSON", str(e))


def check_html(f):
    s = open(f, encoding="utf-8", errors="ignore").read()
    ext = re.findall(r'<(?:script|link|img)[^>]+(?:src|href)="(https?://[^"]+)"', s)
    chk(not ext, f"{f}: no external scripts, styles or images (works offline)", ", ".join(ext[:5]))
    size = os.path.getsize(f)
    chk(size < 15_000_000, f"{f}: size {size:,} bytes is under 15 MB", "")
    NOT.append(f"{f}: page load and filters: run tests/test_web.py (needs a browser)")


for f in A.files:
    if not os.path.exists(f):
        chk(False, f"{f}: exists"); continue
    e = os.path.splitext(f)[1].lower()
    {".xlsx": check_xlsx, ".xlsm": check_xlsx, ".csv": check_csv, ".json": check_json, ".html": check_html}.get(e, lambda x: NOT.append(f"{x}: no checks for this type"))(f)

fails = [r for r in RES if r[0] == "FAIL"]
for s, w, d in RES:
    print(f"{s:4}  {w}" + (f"  [{d}]" if d else ""))
print("NOT CHECKED:")
for n in NOT:
    print("      " + n)
print(f"SUMMARY: {sum(r[0] == 'PASS' for r in RES)} passed, {len(fails)} failed")
sys.exit(1 if fails else 0)
