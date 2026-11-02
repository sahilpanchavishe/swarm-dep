Run from the folder that contains R2/ and R4/ (each with session1_quiet, session2_busy, session3_far):
  python3 analyze_wifi.py   -> per-session loss, bursts, overlap, writes wifi_fit_all.json
  python3 analyze2.py       -> time-in-outage, outages >=2 s, sender-clock check
