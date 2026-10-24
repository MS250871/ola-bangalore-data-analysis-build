"""Append one row to "02 Setup and Log/Analysis Log.md" and verify it landed.

Usage:
  python log_append.py --step "03 Data Inspection" --tool "Claude, Python" \
      --prompt "Inspect every sheet" --output "Created 03 Data Inspection/Data Inspection.md" \
      --check "Review the data dictionary" --decision "Awaiting approval"
Optional: --date YYYY-MM-DD (default today), --root PATH, --correction (prefixes Prompt with CORRECTION:)

Rules enforced: append only, one line per row, no "|" inside cells (replaced by "/"),
line breaks become <br>. Creates the log with its header if missing. Prints the row added."""
import os, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dakit import find_root, LOG_REL, LOG_HEADER, cell, today

ap = argparse.ArgumentParser()
for a in ["step", "tool", "prompt", "output", "check", "decision"]:
    ap.add_argument("--" + a, required=True)
ap.add_argument("--date", default=None)
ap.add_argument("--root", default=None)
ap.add_argument("--correction", action="store_true")
A = ap.parse_args()

root = find_root(A.root)
log = os.path.join(root, LOG_REL)
if not os.path.exists(log):
    with open(log, "w", encoding="utf-8") as fh:
        fh.write("# Analysis Log\n\n" + LOG_HEADER)
prompt = ("CORRECTION: " if A.correction and not A.prompt.startswith("CORRECTION:") else "") + A.prompt
row = "| " + " | ".join(cell(x) for x in [A.date or today(), A.step, A.tool, prompt, A.output, A.check, A.decision]) + " |"
with open(log, "rb") as fh:
    data = fh.read()
nl = b"" if data.endswith(b"\n") or not data else b"\n"
with open(log, "ab") as fh:
    fh.write(nl + row.encode("utf-8") + b"\n")
with open(log, encoding="utf-8") as fh:
    last = [l for l in fh.read().splitlines() if l.strip()][-1]
if last != row:
    sys.exit("ERROR: the new row is not the last line of the log. Check the file.")
print("Log updated.")
print(row)
