"""Headless-browser test for the 09 web dashboard (Python Playwright + Chromium).
Usage: python test_web.py [--dir "09 Web Dashboard"] [--file <prefix>_Web_Dashboard_v1.html]
Reads tests/expected_*.json: {"filters": {"<select id>": "<value>", ...}, "values": {"<data-k>": number|string|null}}
Checks: index.html over http and the standalone file load, no console errors, no external requests,
every data-k value matches (abs tol 0.05 for |v|>2 else 1e-6), Reset returns to expected_all."""
import json, threading, http.server, functools, os, sys, glob, argparse
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser(); ap.add_argument("--dir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); ap.add_argument("--file")
A = ap.parse_args(); DIR = os.path.abspath(A.dir)
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIR); H.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
EXE = os.environ.get("CHROME") or (glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome") or [None])[0]
exps = {os.path.basename(f)[9:-5]: json.load(open(f)) for f in sorted(glob.glob(os.path.join(DIR, "tests", "expected_*.json")))}
standalone = A.file or next(iter(glob.glob(os.path.join(DIR, "*_Web_Dashboard_v*.html"))), None)
res = []
def cmp(page, e, label):
    g = dict(page.eval_on_selector_all("[data-k]", "els => els.map(e => [e.dataset.k, e.dataset.v])")); bad = []
    for k, v in e["values"].items():
        if k not in g: bad.append((k, "missing")); continue
        s = g[k]
        if v is None or isinstance(v, str):
            if (v or "") != (s or ""): bad.append((k, v, s))
            continue
        try: x = float(s)
        except Exception: bad.append((k, v, s)); continue
        if abs(x - v) > (0.05 if abs(v) > 2 else 1e-6): bad.append((k, v, s))
    res.append(("PASS" if not bad else "FAIL", label, f"{len(e['values'])} values, {len(bad)} mismatches", bad[:5]))
def setf(page, filters):
    for sid, val in filters.items():
        page.select_option(f"#{sid}", str(val))
    page.wait_for_timeout(300)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE) if EXE else p.chromium.launch()
    urls = [(f"http://127.0.0.1:{port}/index.html", "index.html over http")]
    if standalone: urls.append(("file://" + os.path.abspath(standalone), "standalone file"))
    for url, label in urls:
        pg = b.new_page(viewport={"width": 1280, "height": 900}); errs, reqs = [], []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None); pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("request", lambda r: reqs.append(r.url))
        pg.goto(url); pg.wait_for_selector("body[data-ready='1']", timeout=15000)
        res.append(("PASS" if not errs else "FAIL", f"{label}: loads without console errors", str(errs[:3]), []))
        ext = [u for u in reqs if not (u.startswith("file://") or u.startswith("http://127.0.0.1") or u.startswith("data:"))]
        res.append(("PASS" if not ext else "FAIL", f"{label}: no external requests", str(ext[:3]), []))
        for name, e in exps.items():
            if e.get("filters"): setf(pg, e["filters"])
            cmp(pg, e, f"{label}: {name}")
            if e.get("filters"):
                pg.click("#reset"); pg.wait_for_timeout(300)
        if "all" in exps: cmp(pg, exps["all"], f"{label}: after Reset")
        pg.close()
    b.close()
for s, l, d, bad in res:
    print(f"{s}  {l}  [{d}]" + (f" {bad}" if bad else ""))
fails = sum(r[0] == "FAIL" for r in res); print(f"SUMMARY: {len(res) - fails} passed, {fails} failed"); sys.exit(1 if fails else 0)
