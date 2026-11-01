# wifi_tx.py - operator side: broadcast numbered UDP packets at 30 Hz over the real Wi-Fi,
# exactly like the RAIST command broadcast. Run on the laptop that would run the gesture pipeline.
# Usage: python wifi_tx.py --minutes 10 --label lab_idle
import argparse, socket, struct, time
ap = argparse.ArgumentParser()
ap.add_argument("--minutes", type=float, default=10); ap.add_argument("--rate", type=float, default=30.0)
ap.add_argument("--port", type=int, default=5006); ap.add_argument("--label", default="session")
ap.add_argument("--dest", default="<broadcast>", help="broadcast address, e.g. 192.168.1.255")
a = ap.parse_args()
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
n = int(a.minutes * 60 * a.rate); t0 = time.perf_counter()
print(f"sending {n} packets at {a.rate} Hz to {a.dest}:{a.port} (label {a.label})")
for seq in range(n):
    target = t0 + seq / a.rate
    while time.perf_counter() < target: time.sleep(0.0005)
    s.sendto(struct.pack("!Id", seq, time.time()) + a.label.encode()[:32], (a.dest, a.port))
print("done")
