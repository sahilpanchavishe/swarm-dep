# wifi_analyze.py
# Reads all receiver logs from data/wifi/ and computes the Wi-Fi burst
# statistics the dependability headline depends on:
#   - loss rate per receiver
#   - burst-length distribution (runs of consecutive dropped packets)
#   - longest outage (worst burst), in packets and seconds at the send rate
#   - shared-burst correlation (how often ALL receivers drop the same packet)
#
# No cross-machine clock sync is used: loss and bursts come from missing
# sequence numbers only. Pass --sent N (the count the sender reported) so a
# packet dropped by everyone at the tail is still counted.
#
# Usage:
#   python3 wifi_analyze.py --sent 18000 --rate 30
#
# Produces data/wifi/wifi_summary.json, data/wifi/burst_lengths_<id>.csv,
# and figures/wifi_burst_distribution.png

import os, glob, csv, json, argparse
from collections import Counter

def runs_of_drops(present, max_seq):
    """Given the set of received seqs, return the list of consecutive-drop
    run lengths over 0..max_seq inclusive."""
    runs = []
    cur = 0
    for s in range(max_seq + 1):
        if s in present:
            if cur > 0:
                runs.append(cur)
            cur = 0
        else:
            cur += 1
    if cur > 0:
        runs.append(cur)
    return runs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sent", type=int, default=None,
                    help="total packets the sender reported (recommended)")
    ap.add_argument("--rate", type=float, default=30.0, help="send rate Hz")
    args = ap.parse_args()

    files = sorted(glob.glob("data/wifi/received_*.csv"))
    if not files:
        print("No receiver logs found in data/wifi/. Run the receivers first.")
        return

    received = {}   # id -> set of seqs
    max_seen = 0
    for path in files:
        rid = os.path.basename(path)[len("received_"):-len(".csv")]
        seqs = set()
        with open(path) as f:
            next(f, None)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                s = int(line.split(",")[0])
                seqs.add(s)
                if s > max_seen:
                    max_seen = s
        received[rid] = seqs

    # Horizon: use the sender's reported count if given, else the max seq seen.
    max_seq = (args.sent - 1) if args.sent else max_seen
    total = max_seq + 1

    summary = {"total_packets": total, "rate_hz": args.rate, "receivers": {}}
    os.makedirs("figures", exist_ok=True)

    print(f"Analyzing {len(received)} receivers over {total} packets "
          f"(seq 0..{max_seq})\n")

    all_burst_lengths = {}
    for rid, seqs in received.items():
        got = len([s for s in seqs if s <= max_seq])
        lost = total - got
        loss_rate = lost / total
        runs = runs_of_drops(seqs, max_seq)
        longest = max(runs) if runs else 0
        mean_burst = (sum(runs) / len(runs)) if runs else 0.0
        all_burst_lengths[rid] = runs

        summary["receivers"][rid] = {
            "received": got,
            "lost": lost,
            "loss_rate": round(loss_rate, 4),
            "n_bursts": len(runs),
            "mean_burst_len": round(mean_burst, 2),
            "longest_burst_pkts": longest,
            "longest_outage_s": round(longest / args.rate, 3),
        }
        print(f"[{rid}] loss={loss_rate*100:5.2f}%  bursts={len(runs):4d}  "
              f"mean_burst={mean_burst:.2f} pkts  "
              f"longest={longest} pkts ({longest/args.rate:.2f} s)")

        # per-receiver burst length histogram CSV
        with open(f"data/wifi/burst_lengths_{rid}.csv", "w") as f:
            f.write("burst_len_pkts,count\n")
            for length, cnt in sorted(Counter(runs).items()):
                f.write(f"{length},{cnt}\n")

    # Shared-burst correlation: of all packets lost by at least one receiver,
    # what fraction were lost by EVERY receiver? High = correlated outages
    # (the "shared burst" the simulator models); low = independent loss.
    if len(received) > 1:
        lost_by = {rid: set(range(total)) - seqs for rid, seqs in received.items()}
        union_lost = set().union(*lost_by.values())
        inter_lost = set(range(total))
        for s in lost_by.values():
            inter_lost &= s
        shared_frac = (len(inter_lost) / len(union_lost)) if union_lost else 0.0
        summary["shared_loss_fraction"] = round(shared_frac, 4)
        print(f"\nShared-burst correlation: {shared_frac*100:.1f}% of lost packets "
              f"were lost by ALL {len(received)} receivers")
        print("  (high -> correlated outages; low -> independent per-robot loss)")

    with open("data/wifi/wifi_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Burst-length distribution plot (log-y to show the heavy tail)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 4))
        for rid, runs in all_burst_lengths.items():
            if not runs:
                continue
            c = Counter(runs)
            xs = sorted(c)
            ys = [c[x] for x in xs]
            ax.plot(xs, ys, "o-", ms=4, label=rid)
        ax.set_yscale("log")
        ax.set_xlabel("Burst length (consecutive packets dropped)")
        ax.set_ylabel("Count (log scale)")
        ax.set_title("Wi-Fi burst-length distribution (log-y shows the heavy tail)")
        ax.legend(title="Receiver")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig("figures/wifi_burst_distribution.png", dpi=200)
        print("\nSaved figures/wifi_burst_distribution.png")
    except ImportError:
        print("\n(matplotlib not available — skipped the plot; CSVs still saved)")

    print("Saved data/wifi/wifi_summary.json")

if __name__ == "__main__":
    main()
