# fit_wifi.py - turn receiver logs into the channel parameters the simulator needs.
# Usage: python wifi/fit_wifi.py wifi/rx_R1_*.csv wifi/rx_R2_*.csv ...   (logs from ONE session)
# Reports per receiver: loss rate, burst-length distribution (packets and ms), Gilbert-Elliott fit,
# longest outage; across receivers: how often bursts overlap (the `common` parameter).
import csv, json, sys, math
RATE = 30.0
logs = {}
for fn in sys.argv[1:]:
    seqs = sorted({int(r["seq"]) for r in csv.DictReader(open(fn))})
    logs[fn.split("/")[-1]] = seqs
lo = min(s[0] for s in logs.values()); hi = max(s[-1] for s in logs.values()); n = hi - lo + 1
out = {"rate_hz": RATE, "packets_sent_window": n, "receivers": {}}
lost_sets = {}
for name, seqs in logs.items():
    got = set(seqs); lost = [i for i in range(lo, hi + 1) if i not in got]; lost_sets[name] = set(lost)
    bursts, run, prev = [], 0, None
    for i in lost:
        run = run + 1 if prev == i - 1 else 1
        if prev is not None and prev != i - 1: bursts.append(run_prev)
        run_prev, prev = run, i
    if lost: bursts.append(run_prev)
    loss = len(lost) / n
    mb = sum(bursts) / len(bursts) if bursts else 0.0
    p_bg = 1 / mb if mb else 1.0; p_gb = p_bg * loss / (1 - loss) if loss < 1 else 1.0
    tail = {f">={k}pkt({1000*k/RATE:.0f}ms)": sum(b >= k for b in bursts) for k in (3, 8, 15, 30, 90)}
    out["receivers"][name] = {"loss_rate": round(loss, 5), "n_bursts": len(bursts),
        "mean_burst_pkts": round(mb, 2), "mean_burst_s": round(mb / RATE, 4),
        "max_burst_s": round(max(bursts, default=0) / RATE, 3), "burst_tail_counts": tail,
        "GE_p_good_to_bad": round(p_gb, 5), "GE_p_bad_to_good": round(p_bg, 5)}
names = list(lost_sets)
if len(names) > 1:
    allsets = [lost_sets[k] for k in names]
    both = set.intersection(*allsets); anyl = set.union(*allsets)
    out["all_receivers_lost_same_packet_frac_of_losses"] = round(len(both) / len(anyl), 4) if anyl else 0
print(json.dumps(out, indent=2))
json.dump(out, open("wifi_fit.json", "w"), indent=2)
print("\nPlug mean loss_rate, mean_burst_s and the overlap fraction (~ common) into sim_v2 / run_study_v2.")
