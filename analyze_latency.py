# analyze_latency.py
# Reads all robot logs and reports the measured latency distribution.
# This is the real measurement that replaces RAIST's assumed 45 ms.

import glob
import numpy as np

latencies = []
for fname in sorted(glob.glob("log_robot_*.csv")):
    with open(fname) as f:
        next(f)  # skip header
        for line in f:
            parts = line.strip().split(",")
            lat = parts[4]
            if lat != "":           # only rows where a command arrived
                latencies.append(float(lat))


latencies = np.array(latencies)

# Save the summary to a file so you never have to re-find these numbers.
import os, json
os.makedirs("data", exist_ok=True)

summary = {
    "n_packets": int(len(latencies)),
    "min_ms": round(float(latencies.min()), 2),
    "median_ms": round(float(np.median(latencies)), 2),
    "mean_ms": round(float(latencies.mean()), 2),
    "max_ms": round(float(latencies.max()), 2),
    "std_ms": round(float(latencies.std()), 2),
}

# Save the summary numbers (for the paper)
with open("data/latency_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

# Save every raw latency value (for histograms / re-analysis)
np.savetxt("data/latency_raw.csv", latencies, fmt="%.4f", header="latency_ms", comments="")

print("Measured command latency:")
for k, v in summary.items():
    print(f"  {k} = {v}")
print("\nSaved to data/latency_summary.json and data/latency_raw.csv")
print(f"Measured command latency over {len(latencies)} received packets:")
print(f"  min    = {latencies.min():.2f} ms")
print(f"  median = {np.median(latencies):.2f} ms")
print(f"  mean   = {latencies.mean():.2f} ms")
print(f"  max    = {latencies.max():.2f} ms")
print(f"  std    = {latencies.std():.2f} ms")