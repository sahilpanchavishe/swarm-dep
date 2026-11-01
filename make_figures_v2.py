# make_figures_v2.py - figures for the corrected model.
import csv, json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from robot import V_MAX, A_MAX
from safety import T_STOP
C = {"8": "#2a78c8", "16": "#e08a1e", "32": "#3a9a52"}

# 1. violation vs loss, one panel per burst length, sim markers + analytic lines
R = [r for r in csv.DictReader(open("data/study_v2.csv")) if r["common"] == "0.0"]
fig, axs = plt.subplots(1, 4, figsize=(13, 3.6), sharey=True)
for ax, b in zip(axs, ("0.033", "0.1", "0.3", "1.0")):
    for N in ("8", "16", "32"):
        c = sorted([r for r in R if r["burst_s"] == b and r["N"] == N], key=lambda r: float(r["loss"]))
        x = [100 * float(r["loss"]) for r in c]
        ax.plot(x, [100 * float(r["analytic_total"]) for r in c], "-", color=C[N], lw=1.5)
        ax.errorbar(x, [100 * float(r["total_violation"]) for r in c],
                    yerr=[100 * float(r["ci95_loss"]) for r in c], fmt="o", ms=4, color=C[N], label=f"N = {N}")
    ax.set_title(f"mean burst {1000*float(b):.0f} ms"); ax.set_xlabel("mean packet loss (%)"); ax.grid(alpha=0.3)
axs[0].set_ylabel("STOP-violation rate (%)")
axs[0].legend(title="markers: simulation\nlines: closed form", fontsize=8, title_fontsize=8)
plt.tight_layout(); plt.savefig("figures/v2_violation_vs_loss_burst.png", dpi=200); plt.close()

# 2. fail-safe timeout trade-off at 10% loss
D = [r for r in csv.DictReader(open("data/design_rule_v2.csv")) if r["loss"] == "0.1" and r["timeout_s"] != "none"]
bound = float(D[0]["slack_bound_s"])
fig, axs = plt.subplots(1, 3, figsize=(12, 3.6), sharey=True)
for ax, b in zip(axs, ("0.1", "0.3", "1.0")):
    c = sorted([r for r in D if r["burst_s"] == b], key=lambda r: float(r["timeout_s"]))
    t = [float(r["timeout_s"]) for r in c]
    ax.plot(t, [100 * float(r["total_violation"]) for r in c], "o-", color="#c0392b", label="safety violations")
    ax.plot(t, [100 * float(r["nuisance_per_robot_3s"]) for r in c], "s-", color="#2a78c8", label="nuisance stops / robot / 3 s")
    ax.axvline(bound, color="grey", ls="--"); ax.text(bound, 0.97, f" analytic bound {bound:.2f} s", transform=ax.get_xaxis_transform(), fontsize=8, color="grey", va="top")
    ax.set_title(f"mean burst {1000*float(b):.0f} ms, 10% loss"); ax.set_xlabel("heartbeat timeout (s)"); ax.grid(alpha=0.3)
axs[0].set_ylabel("rate (%)"); axs[0].legend(fontsize=8)
plt.tight_layout(); plt.savefig("figures/v2_failsafe_timeout.png", dpi=200); plt.close()

# 3. confirmation window: STOP misread flat, delay grows
M = json.load(open("data/misread_vs_window.json"))
W = [e["W"] for e in M["stop"]]
fig, ax = plt.subplots(figsize=(6, 3.6))
ax.errorbar([1000 * e["delay_s"] for e in M["stop"]], [100 * e["p"] for e in M["stop"]],
            yerr=[[100 * (e["p"] - e["ci"][0]) for e in M["stop"]], [100 * (e["ci"][1] - e["p"]) for e in M["stop"]]],
            fmt="o-", color="#c0392b", label="STOP hold misread (95% CI)")
ax.plot([1000 * e["delay_s"] for e in M["stop"]], [100 * e["all_err"] for e in M["stop"]], "s--", color="grey", label="all-gesture error")
ax.set_xlabel("confirmation delay = window / 30 fps (ms)"); ax.set_ylabel("error (%)"); ax.grid(alpha=0.3); ax.legend(fontsize=8)
ax.set_title("Waiting longer does not reduce STOP misreads")
plt.tight_layout(); plt.savefig("figures/v2_confirmation_window.png", dpi=200); plt.close()
print("saved figures/v2_*.png")

# 4. peer relay vs broadcast
import os
if os.path.exists("data/relay_study.csv"):
    Q = list(csv.DictReader(open("data/relay_study.csv")))
    def g(relay, f, b, l, N):
        return [r for r in Q if r["relay"] == str(relay) and float(r["rx_fraction"]) == f and r["burst_s"] == b
                and r["loss"] == l and r["N"] == N][0]
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
    # (a) violation vs N at reference (0.3 s bursts, 10% loss)
    Ns = ["8", "16", "32"]; x = [8, 16, 32]
    axs[0].plot(x, [100 * float(g(0, 0.0, "0.3", "0.1", N)["total_violation"]) for N in Ns], "o-", color="#c0392b", label="broadcast only")
    for f, col in [(0.0, "#1e8449"), (0.5, "#2a78c8"), (1.0, "#7f8c8d")]:
        axs[0].plot(x, [100 * float(g(1, f, "0.3", "0.1", N)["total_violation"]) for N in Ns], "s--", color=col,
                    label=f"peer relay, {int(100*f)}% of loss at receiver")
    axs[0].set_xlabel("swarm size N"); axs[0].set_ylabel("STOP-violation rate (%)"); axs[0].set_xticks(x)
    axs[0].set_title("Mean burst 300 ms, 10% loss"); axs[0].grid(alpha=0.3); axs[0].legend(fontsize=7)
    # (b) benefit vs where bursts occur, N=16
    fs = [0.0, 0.25, 0.5, 0.75, 1.0]
    for b, col in [("0.1", "#e08a1e"), ("0.3", "#2a78c8"), ("1.0", "#8e44ad")]:
        br = [100 * float(g(0, f, b, "0.1", "16")["total_violation"]) for f in fs]
        rl = [100 * float(g(1, f, b, "0.1", "16")["total_violation"]) for f in fs]
        axs[1].plot([100 * f for f in fs], br, "o-", color=col, label=f"broadcast, {1000*float(b):.0f} ms bursts")
        axs[1].plot([100 * f for f in fs], rl, "s--", color=col, label=f"relay, {1000*float(b):.0f} ms bursts")
    axs[1].set_xlabel("share of burst loss at the robot's own receiver (%)"); axs[1].set_ylabel("STOP-violation rate (%)")
    axs[1].set_title("N = 16, 10% loss"); axs[1].grid(alpha=0.3); axs[1].legend(fontsize=7, ncol=2)
    plt.tight_layout(); plt.savefig("figures/v2_peer_relay.png", dpi=200); plt.close()
    print("saved figures/v2_peer_relay.png")
