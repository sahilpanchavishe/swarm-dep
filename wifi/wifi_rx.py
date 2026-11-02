# wifi_rx.py - robot side: log every packet received (sequence number + arrival time).
# Usage: python wifi_rx.py --name R1     (Ctrl+C to stop; prints a live counter every second)
import argparse, socket, struct, time, csv
ap = argparse.ArgumentParser(); ap.add_argument("--name", required=True); ap.add_argument("--port", type=int, default=5006)
a = ap.parse_args()
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(("", a.port))
s.settimeout(0.5)   # so Ctrl+C works on Windows even when no packets arrive
fn = f"rx_{a.name}_{time.strftime('%Y%m%d_%H%M%S')}.csv"
with open(fn, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["seq", "t_rx", "t_tx", "label"]); k = 0; last = -1; tp = time.time()
    print(f"logging to {fn} ... waiting for packets. Ctrl+C to stop.")
    try:
        while True:
            try:
                d, addr = s.recvfrom(64)
            except socket.timeout:
                if time.time() - tp > 2: print(f"  ...nothing received yet/now (total {k})"); tp = time.time()
                continue
            seq, ttx = struct.unpack("!Id", d[:12])
            w.writerow([seq, f"{time.time():.6f}", f"{ttx:.6f}", d[12:].decode(errors="ignore")]); k += 1; last = seq
            if k == 1: print(f"  FIRST PACKET from {addr[0]}")
            if k % 30 == 0: print(f"  received {k} packets (last seq {last})"); f.flush()
    except KeyboardInterrupt:
        pass
print(f"stopped, {k} packets in {fn}")
