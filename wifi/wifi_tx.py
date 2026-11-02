# wifi_tx.py - operator side: broadcast numbered UDP packets at 30 Hz over the real Wi-Fi.
# Usage: python wifi_tx.py --minutes 10 --label lab_quiet
# --dest can be one address or several comma-separated receiver IPs (unicast fallback).
# It prints this laptop's IP and the broadcast address it uses (your IP with last number = 255).
import argparse, socket, struct, time
ap = argparse.ArgumentParser()
ap.add_argument("--minutes", type=float, default=10); ap.add_argument("--rate", type=float, default=30.0)
ap.add_argument("--port", type=int, default=5006); ap.add_argument("--label", default="session")
ap.add_argument("--src", default="", help="this laptop's IP on the measurement network (hotspot host: 192.168.137.1)")
ap.add_argument("--dest", default="auto", help="broadcast address; 'auto' = your IP with last number 255")
a = ap.parse_args()
def my_ip():
    t = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: t.connect(("10.255.255.255", 1)); return t.getsockname()[0]   # sends nothing
    except Exception: return "127.0.0.1"
    finally: t.close()
ip = a.src or my_ip()
dests = [d.strip() for d in (a.dest if a.dest != "auto" else ".".join(ip.split(".")[:3] + ["255"])).split(",")]
dest = ",".join(dests)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
if a.src:
    s.bind((a.src, 0))   # send out of exactly this adapter (needed on a hotspot host)
n = int(a.minutes * 60 * a.rate); t0 = time.perf_counter()
print(f"this laptop IP: {ip}\nsending {n} packets at {a.rate} Hz to {dest}:{a.port} (label {a.label})")
try:
    for seq in range(n):
        target = t0 + seq / a.rate
        while time.perf_counter() < target: time.sleep(0.0005)
        pkt = struct.pack("!Id", seq, time.time()) + a.label.encode()[:32]
        for d in dests: s.sendto(pkt, (d, a.port))
        if seq % 300 == 0: print(f"  sent {seq}/{n}")
except KeyboardInterrupt: print("stopped early")
print("done")
