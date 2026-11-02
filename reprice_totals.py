# reprice_totals.py - the loss-driven violation probability is simulated with the misread switched OFF, and the shared
# misread is added exactly:  total = p + (1 - p) * P_loss.  So changing p needs no new simulation. This rewrites the
# total / analytic / p_misread columns of the result CSVs from the stored channel-only columns, using the primary p.
import csv, json
from sim_v2 import analytic_violation
PM = json.load(open("data/stop_misread_primary.json"))["stop"][0]["p"]
def rewrite(fn, col, post=None):
    rows = list(csv.DictReader(open(fn)))
    for r in rows:
        pl = float(r[col]); r["total_violation"] = round(PM + (1 - PM) * pl, 4)
        if post: post(r)
    with open(fn, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("repriced", fn, len(rows), "rows at p =", round(PM, 4))
def study(r):
    r["p_misread"] = round(PM, 4)
    if r["analytic_total"] != "":
        r["analytic_total"] = round(analytic_violation(int(r["N"]), float(r["loss"]), float(r["burst_s"]), PM)[0], 4)
rewrite("data/study_v2.csv", "p_loss_violation", study)
rewrite("data/design_rule_v2.csv", "loss_violation")
rewrite("data/relay_study.csv", "p_loss_violation")
rewrite("data/trace_study.csv", "p_loss_violation", lambda r: r.__setitem__("p_misread", round(PM, 4)))
