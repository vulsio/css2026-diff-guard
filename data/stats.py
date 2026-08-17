#!/usr/bin/env python3
import csv, re, sys
from datetime import datetime, timedelta, timezone
from collections import defaultdict

import os
TSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guard-failures.tsv")

def src_of(target, explicit=None):
    if explicit: return explicit
    t = target.lower()
    if t.startswith("windows") or t == "microsoft": return "microsoft-cvrf"
    if t.startswith("debian"): return "debian-security-tracker"
    if t.startswith("ubuntu"): return "ubuntu-cve-tracker"
    if t.startswith("cpe"): return "cpe(nvd/vulncheck/jvn...)"
    if t.startswith("alma"): return "alma-errata"
    if t.startswith("rocky"): return "rocky-errata"
    if t.startswith("oracle"): return "oracle-linux"
    if t.startswith("amazon"): return "amazon"
    if t.startswith("fedora") or t.startswith("epel"): return "fedora-api"
    if t.startswith(("opensuse","sles","suse")): return "suse-oval"
    if t.startswith(("rhel","redhat")): return "redhat-vex"
    return "other:" + t

# rows: (run_dt, workflow, target, check, rate, source)
recs = []
runs = []  # (dt, workflow, targets_set)
with open(TSV) as f:
    rd = csv.reader(f, delimiter="\t")
    header = next(rd)
    for row in rd:
        run_id, wf, created, event, kind, checks, fail_rows, digest = row[:8]
        if kind != "guard-trip": continue
        dt = datetime.fromisoformat(created.replace("Z","+00:00"))
        targets = set()
        for ent in fail_rows.split(";;"):
            ent = ent.strip()
            if not ent: continue
            m = re.match(r"^(DB|DET_MASTER|DET_OLD)?:(\S+)\s+(.*)$", ent)
            if not m:
                print("UNPARSED:", ent[:80], file=sys.stderr); continue
            check = m.group(1) or "PERSRC"
            target = m.group(2)
            rest = m.group(3).split()
            explicit_src = None
            # per-source rows (#196 run): first token after target is a source id (non-numeric, no %)
            if rest and not rest[0].endswith("%") and not rest[0].replace(".","").isdigit():
                explicit_src = rest[0]; rest = rest[1:]
            rates = [float(x[:-1]) for x in rest if x.endswith("%")]
            # DB rows: detRate, kbRate[, thr]; DET rows: rate[, thr] after 4 ints
            if check == "DB":
                rate = max(rates[:2]) if len(rates) >= 2 else (rates[0] if rates else 0.0)
            else:
                rate = rates[0] if rates else 0.0
            # 集計の正準ソースは target 由来の族(前後の窓で比較可能にするため)。
            # per-source 化(#196, 07-14)後はレポートに明示ソースが載るので別途保持する。
            recs.append((dt, wf, target, check, rate, src_of(target), explicit_src))
            targets.add(target)
        runs.append((dt, wf, targets))

print(f"# parsed: {len(runs)} guard-trip runs, {len(recs)} FAIL rows\n")

# ---- per-target stats with eventization (gap>24h => new event) ----
by_target = defaultdict(list)
for dt, wf, target, check, rate, src, _esrc in recs:
    by_target[target].append((dt, rate, src))

GAP = timedelta(hours=24)
target_events = {}   # target -> list of (onset_dt, end_dt, nruns, maxrate)
for tgt, lst in by_target.items():
    lst.sort()
    evs = []
    for dt, rate, src in lst:
        if evs and dt - evs[-1][1] <= GAP:
            on, end, n, mx = evs[-1]; evs[-1] = (on, dt, n+1, max(mx, rate))
        else:
            evs.append((dt, dt, 1, rate))
    target_events[tgt] = evs

print("## per-target: runs / events / max-rate / active-span")
rows = []
for tgt, evs in target_events.items():
    nruns = sum(e[2] for e in evs)
    rows.append((nruns, len(evs), max(e[3] for e in evs), tgt, by_target[tgt][0][2]))
rows.sort(reverse=True)
print(f"{'target':<42}{'src':<28}{'runs':>5}{'events':>7}{'max%':>9}")
for nruns, nev, mx, tgt, src in rows:
    print(f"{tgt:<42}{src:<28}{nruns:>5}{nev:>7}{mx:>9.1f}")

# ---- per-source aggregation ----
print("\n## per-source: runs(rows) / target-events / distinct targets / max-rate")
by_src = defaultdict(lambda: [0,0,set(),0.0])
for tgt, evs in target_events.items():
    src = by_target[tgt][0][2]
    s = by_src[src]
    s[0] += sum(e[2] for e in evs); s[1] += len(evs); s[2].add(tgt); s[3] = max(s[3], max(e[3] for e in evs))
print(f"{'source':<30}{'rows':>6}{'events':>8}{'targets':>9}{'max%':>9}")
for src, (nrows, nev, tgts, mx) in sorted(by_src.items(), key=lambda x:-x[1][1]):
    print(f"{src:<30}{nrows:>6}{nev:>8}{len(tgts):>9}{mx:>9.1f}")

# ---- time series ----
WD = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
print("\n## run-level: guard-trip runs by weekday (streak-amplified; UTC)")
c = defaultdict(int)
for dt, wf, targets in runs: c[dt.weekday()] += 1
for i,w in enumerate(WD): print(f"{w}: {c[i]:>3} {'#'*(c[i]//2)}")

print("\n## event-onset: target-event onsets by weekday (UTC)")
onsets = [(evs_i[0], tgt, by_target[tgt][0][2]) for tgt, evs in target_events.items() for evs_i in evs]
c = defaultdict(int)
for on, tgt, src in onsets: c[on.weekday()] += 1
n = len(onsets)
for i,w in enumerate(WD): print(f"{w}: {c[i]:>3} {'#'*c[i]}")
print(f"(n={n} target-events; 週あたり期待値 ~{n/7:.1f})")

print("\n## event-onset by day-of-month bucket")
b = defaultdict(int)
for on, tgt, src in onsets:
    b[("01-10" if on.day<=10 else "11-20" if on.day<=20 else "21-31")] += 1
for k in ["01-10","11-20","21-31"]: print(f"{k}: {b[k]}")

# Patch Tuesday distance for microsoft-cvrf onsets
PT = [datetime(2026,m,d,tzinfo=timezone.utc) for m,d in [(4,14),(5,12),(6,9),(7,14),(8,11)]]
print("\n## microsoft-cvrf target-event onsets vs Patch Tuesday (days after nearest PT)")
c = defaultdict(int)
ms_on = sorted({on.date() for on, tgt, src in onsets if src=="microsoft-cvrf"})
for d in ms_on:
    dd = min((datetime(d.year,d.month,d.day,tzinfo=timezone.utc)-p).days for p in PT if p <= datetime(d.year,d.month,d.day,tzinfo=timezone.utc)+timedelta(days=31))
    deltas = [(datetime(d.year,d.month,d.day,tzinfo=timezone.utc)-p).days for p in PT]
    nearest = min(deltas, key=abs)
    c[nearest]+=1
for k in sorted(c): print(f"PT{k:+d}d: {c[k]}")
print("(onset dates:", ", ".join(str(x) for x in ms_on), ")")

# distinct onset *dates* overall (independent-ish sample size)
dates = sorted({on.date() for on,_,_ in onsets})
print(f"\n## independent-ish sample size: {len(onsets)} target-events on {len(dates)} distinct onset dates over the window")

# ---- cluster-level: merge same-source target-events with onsets within 2 days ----
print("\n## cluster-level (source x onset-window<=2d) — 独立イベント近似")
src_onsets = defaultdict(list)
for on, tgt, src in onsets: src_onsets[src].append(on)
clusters = []  # (src, first_onset, n_target_events)
for src, lst in src_onsets.items():
    lst.sort()
    cur = [lst[0]]
    for dt in lst[1:]:
        if dt - cur[-1] <= timedelta(days=2): cur.append(dt)
        else: clusters.append((src, cur[0], len(cur))); cur=[dt]
    clusters.append((src, cur[0], len(cur)))
clusters.sort(key=lambda x: x[1])
print(f"total clusters: {len(clusters)}")
for src, on, n in clusters:
    print(f"  {on.strftime('%Y-%m-%d %a')}  {src:<28} targets={n}")
c = defaultdict(int); b = defaultdict(int)
for src, on, n in clusters:
    c[on.weekday()] += 1
    b[("01-10" if on.day<=10 else "11-20" if on.day<=20 else "21-31")] += 1
print("\ncluster onsets by weekday:")
for i,w in enumerate(WD): print(f"{w}: {c[i]:>3} {'#'*c[i]}")
print("cluster onsets by day-of-month:")
for k in ["01-10","11-20","21-31"]: print(f"{k}: {b[k]}")
csrc = defaultdict(int)
for src, on, n in clusters: csrc[src]+=1
print("clusters per source:", dict(sorted(csrc.items(), key=lambda x:-x[1])))

# ---- fail sequences: consecutive FAILs per workflow (gap<=9h; a PASS in between forces >=12h gap) ----
print("\n## fail sequences per workflow (gap<=9h)")
by_wf = defaultdict(list)
for dt, wf, targets in runs: by_wf[wf].append(dt)
total = 0
for wf in sorted(by_wf):
    lst = sorted(by_wf[wf]); seqs = []
    for dt in lst:
        if seqs and dt - seqs[-1][1] <= timedelta(hours=9):
            s = seqs[-1]; seqs[-1] = (s[0], dt, s[2]+1)
        else:
            seqs.append((dt, dt, 1))
    total += len(seqs)
    lens = sorted(s[2] for s in seqs)
    lg = max(seqs, key=lambda s: s[2])
    print(f"{wf}: runs={len(lst)} sequences={len(seqs)} median_len={lens[len(lens)//2]} "
          f"longest={lg[2]} ({lg[0]:%m-%d %H:%M}..{lg[1]:%m-%d %H:%M})")
print(f"total sequences: {total}")

# ---- sequence-level analytics ----
# rebuild sequences carrying run payloads (targets+sources per run)
run_payload = defaultdict(list)  # (wf) -> [(dt, {(target,src)})]
tsrc = {}
for dt, wf, target, check, rate, src, _esrc in recs:
    tsrc.setdefault(target, src)  # first wins: #196 run's explicit per-source labels must not relabel earlier generic 'cpe' rows
for dt, wf, targets in runs:
    run_payload[wf].append((dt, {(t, tsrc[t]) for t in targets}))

seq_rows = []  # (wf, onset, end, nruns, sources_all, sources_onset, targets_all)
for wf in sorted(run_payload):
    lst = sorted(run_payload[wf]); cur = None
    for dt, ts in lst:
        if cur and dt - cur[2] <= timedelta(hours=9):
            cur[2] = dt; cur[3] += 1; cur[4] |= ts
        else:
            if cur: seq_rows.append(cur)
            cur = [wf, dt, dt, 1, set(ts), set(ts)]
    if cur: seq_rows.append(cur)
seq_rows.sort(key=lambda s: s[1])

print("\n## sequence table (66 expected)")
print("wf\tonset(UTC)\tend\truns\tdur_h\tonset_sources\tall_sources\tn_targets")
for wf, on, end, n, allts, onts in seq_rows:
    dur = (end - on).total_seconds()/3600
    s_on = ",".join(sorted({s for _, s in onts}))
    s_all = ",".join(sorted({s for _, s in allts}))
    print(f"{wf}\t{on:%Y-%m-%d %H:%M}\t{end:%m-%d %H:%M}\t{n}\t{dur:.0f}\t{s_on}\t{s_all}\t{len({t for t,_ in allts})}")

print("\n## per-source at sequence granularity")
part = defaultdict(lambda: [0, 0, [], []])  # src -> [n_seq, n_seq_onset, lens, durs]
for wf, on, end, n, allts, onts in seq_rows:
    dur = (end - on).total_seconds()/3600
    for s in {s for _, s in allts}:
        p = part[s]; p[0] += 1; p[2].append(n); p[3].append(dur)
    for s in {s for _, s in onts}:
        part[s][1] += 1
print(f"{'source':<30}{'seqs':>5}{'at-onset':>9}{'len med/max':>13}{'dur_h med/max':>15}")
for s, (nsq, non, lens, durs) in sorted(part.items(), key=lambda x: -x[1][0]):
    lens.sort(); durs.sort()
    print(f"{s:<30}{nsq:>5}{non:>9}{lens[len(lens)//2]:>7}/{max(lens):<5}{durs[len(durs)//2]:>9.0f}/{max(durs):<5.0f}")

print("\n## sequence onsets by weekday / day-of-month (n=%d)" % len(seq_rows))
c = defaultdict(int); b = defaultdict(int)
for wf, on, *_ in seq_rows:
    c[on.weekday()] += 1
    b[("01-10" if on.day<=10 else "11-20" if on.day<=20 else "21-31")] += 1
for i, w in enumerate(WD): print(f"{w}: {c[i]:>3} {'#'*c[i]}")
for k in ["01-10","11-20","21-31"]: print(f"{k}: {b[k]}")

print("\n## sequence length / duration distribution")
lens = sorted(s[3] for s in seq_rows); durs = sorted((s[2]-s[1]).total_seconds()/3600 for s in seq_rows)
import statistics as st
print(f"runs per seq: min {lens[0]} / med {lens[len(lens)//2]} / p90 {lens[int(len(lens)*0.9)]} / max {lens[-1]}")
print(f"first-fail..last-fail hours: med {durs[len(durs)//2]:.0f} / p90 {durs[int(len(durs)*0.9)]:.0f} / max {durs[-1]:.0f}")
onehit = sum(1 for x in lens if x == 1)
print(f"single-run sequences: {onehit}/{len(lens)}")

# ---- source-episodes: per-source FAIL presence merged across workflows, gap<=24h => one episode ----
# The canonical independent-event unit: tracks entry/exit of each source inside/across sequences,
# merges main/nightly tandem, and splits distinct flare-ups sharing one sequence.
print("\n## source-episodes (main/nightly merged, gap<=24h)")
src_runs = defaultdict(dict)  # src -> {dt: (wfset, targets, maxrate)}
for dt, wf, target, check, rate, src, _esrc in recs:
    ent = src_runs[src].setdefault(dt, [set(), set(), 0.0])
    ent[0].add("M" if wf == "DB" else "N"); ent[1].add(target); ent[2] = max(ent[2], rate)

episodes = []  # (src, onset, end, nruns, wfs, targets, maxrate)
for src, d in src_runs.items():
    items = sorted(d.items())
    cur = None
    for dt, (wfs, tgts, mx) in items:
        if cur and dt - cur[2] <= timedelta(hours=24):
            cur[2] = dt; cur[3] += 1; cur[4] |= wfs; cur[5] |= tgts; cur[6] = max(cur[6], mx)
        else:
            if cur: episodes.append(cur)
            cur = [src, dt, dt, 1, set(wfs), set(tgts), mx]
    if cur: episodes.append(cur)
episodes.sort(key=lambda e: e[1])

print(f"total source-episodes: {len(episodes)}")
print("onset(UTC)\tend\tsource\truns\tdur_h\twf\tn_tgt\tmax%")
for src, on, end, n, wfs, tgts, mx in episodes:
    print(f"{on:%Y-%m-%d %H:%M}\t{end:%m-%d %H:%M}\t{src}\t{n}\t{(end-on).total_seconds()/3600:.0f}\t{'+'.join(sorted(wfs))}\t{len(tgts)}\t{mx:.1f}")

print("\n## per-source at episode granularity")
agg = defaultdict(lambda: [0, [], [], 0.0, 0, 0])  # src -> [n_ep, durs, ntgts, maxrate, both_wf, main_involved]
for src, on, end, n, wfs, tgts, mx in episodes:
    a = agg[src]; a[0] += 1; a[1].append((end-on).total_seconds()/3600); a[2].append(len(tgts))
    a[3] = max(a[3], mx); a[4] += 1 if len(wfs) == 2 else 0; a[5] += 1 if "M" in wfs else 0
print(f"{'source':<30}{'episodes':>9}{'main-inv':>9}{'both-wf':>8}{'dur_h med/max':>15}{'tgts med/max':>14}{'max%':>9}")
for src, (nep, durs, ntg, mx, both, minv) in sorted(agg.items(), key=lambda x: (-x[1][5], -x[1][0])):
    durs.sort(); ntg.sort()
    print(f"{src:<30}{nep:>9}{minv:>9}{both:>8}{durs[len(durs)//2]:>9.0f}/{durs[-1]:<5.0f}{ntg[len(ntg)//2]:>8}/{ntg[-1]:<5}{mx:>9.1f}")

print("\n## episode onsets by weekday / day-of-month (n=%d)" % len(episodes))
c = defaultdict(int); b = defaultdict(int)
for src, on, *_ in episodes:
    c[on.weekday()] += 1
    b[("01-10" if on.day<=10 else "11-20" if on.day<=20 else "21-31")] += 1
for i, w in enumerate(WD): print(f"{w}: {c[i]:>3} {'#'*c[i]}")
for k in ["01-10","11-20","21-31"]: print(f"{k}: {b[k]}")


# ---- per-source 化(#196, 2026-07-14)後: レポート明示ソースによる内訳 ----
PERSRC_FROM = datetime(2026,7,14,7,0,tzinfo=timezone.utc)
print("\n## explicit-source breakdown (per-source 化後の窓のみ)")
es_rows = defaultdict(lambda: [0,set(),0.0])
for dt, wf, target, check, rate, src, esrc in recs:
    if dt < PERSRC_FROM or not esrc: continue
    r = es_rows[esrc]
    r[0]+=1; r[1].add(target); r[2]=max(r[2],rate)
print(f"{'explicit source':<32}{'rows':>6}{'targets':>9}{'max%':>10}")
for esrc,(n,tg,mx) in sorted(es_rows.items(), key=lambda x:-x[1][0]):
    print(f"{esrc:<32}{n:>6}{len(tg):>9}{mx:>10.1f}")
tot = sum(v[0] for v in es_rows.values())
print(f"(rows with explicit source: {tot})")
