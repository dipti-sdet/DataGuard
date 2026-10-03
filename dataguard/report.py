"""Builds a self-contained HTML report (no external files) from run_suite() results."""
import datetime
import html

from .bugs import BUGS
from .checks import CHECKS

CSS = """
:root{--bg:#fff;--fg:#1c1e21;--muted:#65676b;--card:#f5f6f7;--line:#dddfe2;--ok:#1a7f37;--okbg:#dafbe1;--bad:#c62828;--badbg:#ffe3e3;--acc:#0b5fff}
@media(prefers-color-scheme:dark){:root{--bg:#16181c;--fg:#e8e9ea;--muted:#9aa0a6;--card:#22252a;--line:#343840;--ok:#56d364;--okbg:#12361c;--bad:#ff8a80;--badbg:#3d1b1b;--acc:#6ea8ff}}
*{box-sizing:border-box}body{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;max-width:1100px;margin-inline:auto}
h1{font-size:1.5rem;margin:.2rem 0}h2{font-size:1.15rem;margin:1.8rem 0 .6rem;border-bottom:1px solid var(--line);padding-bottom:.3rem}
.sub{color:var(--muted);font-size:.85rem}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0}
.kpi{background:var(--card);border-radius:10px;padding:12px}.kpi b{display:block;font-size:1.6rem}.kpi span{color:var(--muted);font-size:.8rem}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:8px}table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{background:var(--card);position:sticky;top:0}
td.c,th.c{text-align:center}.pass{color:var(--ok);background:var(--okbg);font-weight:600;text-align:center}.fail{color:var(--bad);background:var(--badbg);font-weight:600;text-align:center}
.chip{display:inline-block;background:var(--badbg);color:var(--bad);border-radius:10px;padding:0 7px;margin:1px;font-size:.75rem;font-weight:600}
.chip.ok{background:var(--okbg);color:var(--ok)}code{background:var(--card);padding:0 4px;border-radius:4px}
details{background:var(--card);border-radius:8px;padding:8px 12px;margin:8px 0}summary{cursor:pointer;font-weight:600}
li{margin:3px 0;font-size:.85rem}.tag{color:var(--acc);font-weight:600}
"""


def _failed(res):
    return [c.id for c in CHECKS if not res[c.id][0]]


def render(runs, path):
    good = runs[0][2]
    bug_runs = runs[1:]
    good_pass = sum(1 for ok, _ in good.values() if ok)
    detected = sum(1 for _, _, res in bug_runs if _failed(res))
    now = datetime.datetime.now().strftime("%d %b %Y, %H:%M")
    e = html.escape
    out = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
           f"<title>DataGuard validation report</title><style>{CSS}</style></head><body>",
           "<h1>DataGuard validation report</h1>",
           f"<div class='sub'>SQL-based incremental ETL validation &middot; generated {now}</div>",
           "<div class='kpis'>"
           f"<div class='kpi'><b>{len(CHECKS)}</b><span>checks defined</span></div>"
           f"<div class='kpi'><b>{good_pass}/{len(CHECKS)}</b><span>pass on the GOOD run (must be all)</span></div>"
           f"<div class='kpi'><b>{len(bug_runs)}</b><span>bugs planted</span></div>"
           f"<div class='kpi'><b>{detected}/{len(bug_runs)}</b><span>bugs detected</span></div></div>"]

    verdict = ("All checks pass on the good run and every planted bug is caught."
               if good_pass == len(CHECKS) and detected == len(bug_runs)
               else "Attention: the good run has failures or a bug went undetected.")
    out.append(f"<p><b>{verdict}</b></p>")

    # 1. bug detection table
    out.append("<h2>1. Bug detection</h2><div class='scroll'><table><tr><th>Bug</th><th>Type</th><th>What is wrong</th>"
               "<th class='c'>Caught?</th><th>Failing checks</th></tr>")
    for bug_id, _, res in bug_runs:
        b = BUGS[bug_id]
        failed = _failed(res)
        chips = "".join(f"<span class='chip{' ok' if c in b['detectors'] else ''}' title='green = documented primary detector'>{c}</span>" for c in failed)
        out.append(f"<tr><td><b>{bug_id}</b></td><td>{e(b['type'])}</td><td>{e(b['what'])}<div class='sub'>planted in <code>{b['file']}</code></div></td>"
                   f"<td class='{'pass' if failed else 'fail'}'>{'YES' if failed else 'NO'}</td><td>{len(failed)}: {chips}</td></tr>")
    out.append("</table></div><div class='sub'>Green chips = the check designed to catch that bug. Red chips = other checks that also failed (side effects).</div>")

    # 2. heatmap
    out.append("<h2>2. Check x run matrix</h2><div class='scroll'><table><tr><th>ID</th><th>Category</th><th>Check</th><th class='c'>GOOD</th>")
    for bug_id, _, _ in bug_runs:
        out.append(f"<th class='c' title='{e(BUGS[bug_id]['type'])}'>{bug_id}</th>")
    out.append("</tr>")
    for chk in CHECKS:
        out.append(f"<tr><td><b>{chk.id}</b></td><td>{e(chk.category)}</td><td>{e(chk.title)}</td>")
        for _, _, res in [runs[0]] + bug_runs:
            ok = res[chk.id][0]
            out.append(f"<td class='{'pass' if ok else 'fail'}'>{'&#10003;' if ok else '&#10007;'}</td>")
        out.append("</tr>")
    out.append("</table></div><div class='sub'>Reading it: the GOOD column must be all green. Each bug column should have red cells.</div>")

    # 3. coverage
    out.append("<h2>3. Coverage by test category</h2><div class='scroll'><table><tr><th>Category</th><th class='c'>Checks</th><th>Bugs that trip it</th></tr>")
    cats = []
    for chk in CHECKS:
        if chk.category not in cats:
            cats.append(chk.category)
    for cat in cats:
        ids = [c.id for c in CHECKS if c.category == cat]
        tripped = [bid for bid, _, res in bug_runs if any(not res[i][0] for i in ids)]
        out.append(f"<tr><td>{e(cat)}</td><td class='c'>{len(ids)}</td><td>{' '.join(f'<span class=chip>{b}</span>' for b in tripped) or '-'}</td></tr>")
    out.append("</table></div>")

    # 4. failure details
    out.append("<h2>4. Failure details (expected vs actual)</h2>")
    for bug_id, _, res in bug_runs:
        failed = [c for c in CHECKS if not res[c.id][0]]
        out.append(f"<details><summary>{bug_id}: {e(BUGS[bug_id]['type'])} ({len(failed)} failing)</summary><ul>")
        for chk in failed[:12]:
            out.append(f"<li><span class='tag'>{chk.id}</span> {e(chk.title)}<br><span class='sub'>{e(str(res[chk.id][1])[:300])}</span></li>")
        if len(failed) > 12:
            out.append(f"<li class='sub'>... and {len(failed) - 12} more</li>")
        out.append("</ul></details>")
    out.append("</body></html>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(out))


def print_summary(runs):
    good = runs[0][2]
    print(f"\nGOOD run: {sum(1 for ok, _ in good.values() if ok)}/{len(CHECKS)} checks passed")
    print(f"{'bug':5}{'caught':8}{'failing':9}type")
    for bug_id, _, res in runs[1:]:
        n = len(_failed(res))
        print(f"{bug_id:5}{'YES' if n else 'NO':8}{n:<9}{BUGS[bug_id]['type']}")
