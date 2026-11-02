# Wi-Fi burst measurement, 2026-11-02 (first real channel data)

Setup: sender = Windows laptop hosting Mobile Hotspot (2.4 GHz), also a client of an iPhone hotspot (shared radio). 30 Hz UDP broadcast,
10 min/session, 18000 packets. Receivers: R2, R4 (Macs). R3 excluded (0 packets in setup test). R1 (Windows) excluded: ~20% reception at 2-3 m
(receiver-side broadcast problem, not channel). Layout: S1 quiet, R2+R4 side by side (30 cm); S2 busy (6 devices streaming YouTube), R2 3 m, R4 2.5 m;
S3 far, R2 same spot, R4 in another room 8 m.

| Session | Rx | loss | mean burst | longest | bursts>=8 pkt (267 ms) | P(miss STOP window, k=8) | iid-model prediction |
|---|---|---|---|---|---|---|---|
| quiet | R2 | 2.0% | 53 ms | 0.6 s | 7 | 0.15% | 3e-12 |
| quiet | R4 | 2.7% | 60 ms | 1.2 s | 7 | 0.28% | 3e-11 |
| busy | R2 | 3.7% | 51 ms | 0.4 s | 10 | 0.14% | 3e-10 |
| busy | R4 | 9.0% | 68 ms | 0.9 s | 28 | 0.43% | 4e-07 |
| far | R2 | 7.5% | 57 ms | 9.0 s (single event) | 10 | 1.6% | 1e-07 |
| far | R4 | 42% | 130 ms | 5.2 s | 274 | 10.1% | 0.098 |

Findings: (1) losses are bursty, orders of magnitude worse than an iid model predicts for the same mean loss; (2) a 2-state Gilbert-Elliott with geometric bursts
underestimates the tail (use trace replay); (3) side-by-side receivers share few losses (quiet: 14%/11% of each other's losses, ~5x chance; far: ~independent);
(4) R2's 9 s outage at t=291.7 s coincides with a ~29 s sender wall-clock step at seq 8700 -> probable sender/hotspot disturbance, unconfirmed;
(5) receiver hardware differs (R4 lost 2.4x more than R2 at similar distance in S2).
Caveats: one day, one hotspot, two receivers, 10 min each; sender radio shared with iPhone link.
Files: analyze_wifi.py, analyze2.py, wifi_fit_all.json.
