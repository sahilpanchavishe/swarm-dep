# wifi_rx.py - robot side: log every packet received (sequence number + arrival time).
# Run on each receiver (laptops standing in for robots, placed where robots would be).
# Usage: python wifi_rx.py --name R1     (Ctrl+C when the sender says done)
import argparse, socket, struct, time, csv
ap = argparse.ArgumentParser(); ap.add_argument("--name", required=True); ap.add_argument("--port", type=int, default=5006)
a = ap.parse_args()
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(("", a.port))
fn = f"rx_{a.name}_{time.strftime('%Y%m%d_%H%M%S')}.csv"
with open(fn, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["seq", "t_rx", "t_tx", "label"]); k = 0
    print(f"logging to {fn} ... Ctrl+C to stop")
    try:
        while True:
            d, _ = s.recvfrom(64); seq, ttx = struct.unpack("!Id", d[:12])
            w.writerow([seq, f"{time.time():.6f}", f"{ttx:.6f}", d[12:].decode(errors="ignore")]); k += 1
            if k % 900 == 0: print(f"  {k} packets"); f.flush()
    except KeyboardInterrupt:
        print(f"stopped, {k} packets in {fn}")
