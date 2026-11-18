"""Local validation for main.py (dev tool, not part of the entry).

1. Runs main.py's CLI on the 4 practice cases, checks output shape/size,
   determinism (two runs byte-identical) and runtime.
2. Scores v2 vs the starter against SullyGnome practice answers
   (/tmp/twitch-work/practice_answers.json).
3. Leave-one-comparable-out: each comparable as a pseudo-case, forecast
   from the other 36, scored on its own release day.
Run: python3 validate.py [kit_input_dir]
"""
import json, math, os, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import main as entry
sys.path.insert(0, '/tmp/twitch-work')
from score import score_case, starter_forecast

KIT = Path(sys.argv[1] if len(sys.argv) > 1 else
           '/tmp/twitch-kit/unpacked/gta6-twitch-ccu-forecast-01-kit/input')
ANS = json.load(open('/tmp/twitch-work/practice_answers.json'))
ANS = {k: {int(h): v for h, v in vv.items()} for k, vv in ANS.items()}

def check_output(path, case):
    raw = path.read_bytes()
    assert len(raw) <= 65536, f"{path} too large: {len(raw)}"
    obj = json.loads(raw)
    assert set(obj) == {"hours"}, obj.keys()
    assert len(obj["hours"]) == 23
    seen = set()
    for row in obj["hours"]:
        assert set(row) == {"hour", "q"}, row
        assert row["hour"] not in seen and 2 <= row["hour"] <= 24
        seen.add(row["hour"])
        q = row["q"]
        assert len(q) == 5 and all(0 < v <= 1e9 for v in q)
        assert all(q[i] <= q[i+1] for i in range(4)), row
    return obj

print("=== 1. CLI run on practice cases ===")
outdir = Path('/tmp/twitch-work/out_v2')
for run in (1, 2):
    if outdir.exists():
        for f in outdir.glob('*'): f.unlink()
    env = dict(os.environ, MAKEFUN_INPUT_DIR=str(KIT), MAKEFUN_OUTPUT_DIR=str(outdir))
    t0 = time.time()
    r = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / 'main.py')],
                       env=env, capture_output=True, text=True)
    dt = time.time() - t0
    assert r.returncode == 0, r.stderr
    print(f"run {run}: rc=0 in {dt:.2f}s")
    blobs = {f.name: f.read_bytes() for f in sorted(outdir.glob('*.out'))}
    if run == 1:
        first = blobs
        for f in sorted(outdir.glob('*.out')):
            case = json.loads((KIT / f.name.replace('.out', '.in')).read_text())
            check_output(f, case)
        print("  shape/size/monotonicity checks: OK for", sorted(blobs))
    else:
        assert blobs == first, "non-deterministic output between runs!"
        print("  determinism: two runs byte-identical: OK")

print("\n=== 2. Practice p00-p03: v2 vs starter ===")
tot_v2, tot_st = [], []
for cid in ['p00', 'p01', 'p02', 'p03']:
    case = json.loads((KIT / f'{cid}.in').read_text())
    p1 = case['known'][0]['viewers']
    v2 = entry.forecast_case(case)
    fc_v2 = {row['hour']: row['q'] for row in v2['hours']}
    fc_st = starter_forecast(p1)
    l2, m2, c2 = score_case(ANS[cid], fc_v2)
    l1, m1, c1 = score_case(ANS[cid], fc_st)
    tot_v2.append(l2); tot_st.append(l1)
    print(f"{cid} p1={p1:7,.0f}: v2 loss={l2:.4f} miss={m2:5.1f}% cov={c2:.3f} | "
          f"starter loss={l1:.4f} miss={m1:5.1f}% cov={c1:.3f}")
import statistics
print(f"MEAN: v2 loss={statistics.mean(tot_v2):.4f} | starter loss={statistics.mean(tot_st):.4f} "
      f"| current entry (server) 0.304 | house baseline 0.387")

print("\n=== 3. Leave-one-comparable-out (forecast_case itself) ===")
d = json.loads((KIT / 'p00.in').read_text())
raw_comps = d['comparables']
# usable comps with a day curve
from datetime import datetime, timedelta
def parse(t): return datetime.fromisoformat(t.replace('Z', '+00:00'))
def day_curve(comp):
    ds = parse(comp['day_start']); out = {}
    for h in comp['hourly']:
        t = parse(h['from'])
        if ds <= t < ds + timedelta(days=1) and h['viewers']:
            out[t.hour+1] = h['viewers']
    return out
usable = [(c, day_curve(c)) for c in raw_comps]
usable = [(c, day) for c, day in usable if day.get(1)]
print(f"usable comparables: {len(usable)}")
for label, subset in [("all", usable), ("big h1>=20000", [u for u in usable if u[1][1] >= 20000])]:
    losses = []
    for i, (comp, day) in enumerate(subset):
        train = [c for j, (c, _) in enumerate(usable) if usable[j][0] is not comp]
        # pseudo-case: known h1, forecast h2..24, comparables = train raw dicts
        case = {"levels": [0.05, 0.25, 0.5, 0.75, 0.95],
                "known": [{"hour": 1, "viewers": day[1]}],
                "forecast": [{"hour": h} for h in range(2, 25)],
                "comparables": train}
        fc = entry.forecast_case(case)
        truth = {h: day[h] for h in range(2, 25) if day.get(h)}
        l, m, cv = score_case(truth, {r['hour']: r['q'] for r in fc['hours']})
        losses.append(l)
    print(f"LOCO {label}: mean loss={statistics.mean(losses):.4f} (n={len(losses)})")
