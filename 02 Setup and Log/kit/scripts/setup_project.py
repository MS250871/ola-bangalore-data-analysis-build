"""Create a new Data Analysis Build project in the current folder (or --root).

Usage:
  python setup_project.py --root "<project folder>" --name "Global Superstore Sales Analysis" \
     --purpose "..." --audience "..." --prefix Global_Superstore \
     [--question-target 8] [--publish-target "Claude artifact"] [--platform "Claude desktop"] \
     [--no-excel] [--no-web]

What it does (never touches files inside Raw Data, never overwrites an existing file):
- creates the 11 numbered folders (Raw Data is created only if missing)
- writes PROJECT_RULES.md, CLAUDE.md, AGENTS.md, 02 Setup and Log/Setup.md, Analysis Log.md, project.json
- copies the kit (scripts, templates, prompts) into 02 Setup and Log/kit so the project is self-contained
- records SHA-256 fingerprints of every file in Raw Data
- checks Python packages and prints a summary"""
import os, sys, json, shutil, argparse, importlib, platform as _pf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from dakit import FOLDERS, LOG_HEADER, CFG_REL, sha256, raw_files, today, save_cfg, load_cfg

ap = argparse.ArgumentParser()
ap.add_argument("--root", default=os.getcwd())
ap.add_argument("--name", required=True)
ap.add_argument("--purpose", required=True)
ap.add_argument("--audience", default="Business leadership")
ap.add_argument("--prefix", required=True, help="file prefix, letters/digits/underscores, e.g. Global_Superstore")
ap.add_argument("--question-target", type=int, default=8)
ap.add_argument("--publish-target", default="Claude artifact (or ChatGPT canvas or Sites when working in ChatGPT)")
ap.add_argument("--platform", default="not recorded")
ap.add_argument("--no-excel", action="store_true")
ap.add_argument("--no-web", action="store_true")
A = ap.parse_args()

root = os.path.abspath(A.root)
skill_dir = os.path.dirname(HERE)
tpl_dir = os.path.join(skill_dir, "assets", "templates")
prefix = "".join(c if c.isalnum() else "_" for c in A.prefix).strip("_")
created, kept = [], []

for f in FOLDERS:
    p = os.path.join(root, f)
    if os.path.isdir(p):
        kept.append(f + "/")
    else:
        os.makedirs(p)
        created.append(f + "/")

# kit copy (scripts + templates + prompts); refreshed only if absent so a project keeps its kit version
kit = os.path.join(root, "02 Setup and Log", "kit")
if not os.path.exists(kit):
    os.makedirs(kit)
    shutil.copytree(HERE, os.path.join(kit, "scripts"), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(os.path.join(skill_dir, "assets"), os.path.join(kit, "assets"), ignore=shutil.ignore_patterns("__pycache__"))
    with open(os.path.join(kit, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("# Kit\n\nScripts and templates copied from the Data Analysis Build kit at setup "
                 f"({today()}). Do not edit by hand. The step skills call these scripts.\n")
    created.append("02 Setup and Log/kit/")
else:
    kept.append("02 Setup and Log/kit/")

# raw files
raws = raw_files(root)
cfg = load_cfg(root)
cfg.update({
    "project_name": A.name, "purpose": A.purpose, "audience": A.audience, "file_prefix": prefix,
    "question_target": A.question_target, "selected_questions": cfg.get("selected_questions"),
    "outputs": {"excel_dashboard": not A.no_excel, "web_dashboard": not A.no_web},
    "publish_target": A.publish_target, "platform": A.platform,
    "kit_version": "1.0.0", "created": cfg.get("created", today()),
})
rec = cfg.setdefault("raw_hashes", {})
for p in raws:
    k = os.path.relpath(p, root).replace("\\", "/")
    rec.setdefault(k, {"sha256": sha256(p), "bytes": os.path.getsize(p), "recorded": today()})
cfg.setdefault("sources", [k for k in rec])
for k in ["measures", "filters", "date_field", "keys"]:
    cfg.setdefault(k, [] if k != "date_field" else "")
os.makedirs(os.path.dirname(os.path.join(root, CFG_REL)), exist_ok=True)
save_cfg(root, cfg)

# package check
pk = []
for m in ["pandas", "openpyxl"]:
    try:
        v = importlib.import_module(m).__version__
        pk.append((m, v))
    except Exception:
        pk.append((m, "MISSING"))
tools = ["- **AI assistant** (" + A.platform + "): planning, documents, scripts, logging."]
tools.append("- **Python " + _pf.python_version() + "** with " + ", ".join(f"**{m} {v}**" for m, v in pk) +
             f": inspection, quality checks, cleaning, workbook builds (checked {today()}).")
tools += ["- **Microsoft Excel (desktop)**: the user opens every workbook at its gate and reports whether a repair prompt appears.",
          "- **Web browser**: viewing the HTML dashboard.",
          f"- **Publishing**: {A.publish_target}, only after explicit approval."]
raw_tbl = "| File | Size (bytes) | SHA-256 (recorded) |\n|------|------|------|\n" + \
          "".join(f"| `{k}` | {v['bytes']:,} | `{v['sha256']}` ({v['recorded']}) |\n" for k, v in rec.items()) if rec else \
          "No files in `Raw Data` yet. Add the source files, then run `raw_guard.py --record`."

subs = {"{{PROJECT_NAME}}": A.name, "{{PURPOSE}}": A.purpose, "{{AUDIENCE}}": A.audience, "{{PREFIX}}": prefix,
        "{{QUESTION_TARGET}}": str(A.question_target), "{{PUBLISH_TARGET}}": A.publish_target,
        "{{PLATFORM}}": A.platform, "{{ROOT}}": root, "{{RAW_TABLE}}": raw_tbl, "{{TOOLS}}": "\n".join(tools)}


def render(src, dst):
    if os.path.exists(dst):
        kept.append(os.path.relpath(dst, root)); return
    with open(os.path.join(tpl_dir, src), encoding="utf-8") as fh:
        t = fh.read()
    for k, v in subs.items():
        t = t.replace(k, v)
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(t)
    created.append(os.path.relpath(dst, root))


render("PROJECT_RULES.md", os.path.join(root, "PROJECT_RULES.md"))
render("CLAUDE.md", os.path.join(root, "CLAUDE.md"))
render("AGENTS.md", os.path.join(root, "AGENTS.md"))
render("Setup.md", os.path.join(root, "02 Setup and Log", "Setup.md"))
log = os.path.join(root, "02 Setup and Log", "Analysis Log.md")
if not os.path.exists(log):
    with open(log, "w", encoding="utf-8") as fh:
        fh.write(f"# Analysis Log: {A.name}\n\n" + LOG_HEADER)
    created.append(os.path.relpath(log, root))
else:
    kept.append(os.path.relpath(log, root))

print("CREATED:", *created, sep="\n  ")
print("ALREADY EXISTED (left unchanged):", *(kept or ["none"]), sep="\n  ")
print("RAW FILES RECORDED:", len(rec))
for k, v in rec.items():
    print(f"  {k}  {v['bytes']:,} bytes  sha256={v['sha256'][:16]}...")
print("PACKAGES:", ", ".join(f"{m} {v}" for m, v in pk))
if any(v == "MISSING" for _, v in pk):
    print("WARNING: install missing packages with: python -m pip install pandas openpyxl")
