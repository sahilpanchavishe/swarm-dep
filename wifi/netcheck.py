# netcheck.py - tells you EXACTLY why packets are not arriving, with PASS/FAIL messages.
# On every RECEIVER:   python netcheck.py listen
# On the SENDER:       python netcheck.py probe --to RECEIVER_IP1,RECEIVER_IP2
import argparse, socket, time
PORT = 5007
def my_ip():
    t = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: t.connect(("10.255.255.255", 1)); return t.getsockname()[0]
    except Exception: return "unknown"
    finally: t.close()
ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["listen", "probe"])
ap.add_argument("--to", default=""); ap.add_argument("--src", default=""); a = ap.parse_args(); ip = my_ip()
print(f"This laptop's Wi-Fi IP: {ip}")
if a.mode == "listen":
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", PORT)); s.settimeout(0.5); print("Listening. Ctrl+C to stop. Each packet that arrives is shown below:")
    try:
        while True:
            try: d, addr = s.recvfrom(100)
            except socket.timeout: continue
            print(f"  GOT {d[:20]!r} from {addr[0]}   (this proves the packet reached this laptop)")
            s.sendto(b"ECHO " + d, addr)
    except KeyboardInterrupt: pass
else:
    targets = [x.strip() for x in a.to.split(",") if x.strip()]
    if not targets: raise SystemExit("give --to IP1,IP2")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    if a.src: s.bind((a.src, 0))
    s.settimeout(0.3)
    def probe(dest, n=8):
        heard = set()
        for i in range(n):
            s.sendto(f"probe{i}".encode(), (dest, PORT)); t0 = time.time()
            while time.time() - t0 < 0.5:
                try: d, addr = s.recvfrom(100); heard.add((addr[0], d[:12]))
                except socket.timeout: pass
        return heard
    allok = True
    for t in targets:
        h = probe(t); n = len({x[1] for x in h if x[0] == t})
        print(f"UNICAST to {t}: echoes {n}/8 -> " + ("PASS" if n >= 6 else "FAIL")); allok &= n >= 6
        if n < 6: print("   Look at that receiver's screen. If it shows GOT lines, the packet arrives but the reply is blocked (sender firewall).\n"
                        "   If it shows nothing: the packet never arrived -> router client-isolation, different network, or receiver firewall.")
    b = ".".join(targets[0].split(".")[:3] + ["255"]); h = probe(b)
    who = sorted({x[0] for x in h}); print(f"BROADCAST to {b}: answered by {who if who else 'nobody'} -> " + ("PASS" if who else "FAIL"))
    print("\nVERDICT:")
    if not allok: print("  Receivers cannot be reached at all. Fix this first (see guide, section 4). Do NOT start the measurements.")
    elif not who: print("  Direct packets work, broadcast is blocked. Use  --dest IP1,IP2  mode in wifi_tx.py (results = lower bound on loss).")
    else: print("  Everything works. You can run wifi_tx.py without --dest (real broadcast) or with it.")
