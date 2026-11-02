# wifi_sender.py
# Broadcasts a 30 Hz UDP stream for a fixed duration, like the RAIST
# rebroadcast rate. Each packet carries a sequence number and a send
# timestamp. Run this on ONE laptop. The receivers log what arrives.
#
# Usage:
#   python3 wifi_sender.py --rate 30 --minutes 10 --port 5005
#
# All devices (sender + receivers) must be on the SAME Wi-Fi network.

import socket
import time
import json
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", type=float, default=30.0, help="packets per second")
    ap.add_argument("--minutes", type=float, default=10.0, help="run duration")
    ap.add_argument("--port", type=int, default=5005)
    ap.add_argument("--session", default="session", help="label saved in each packet")
    args = ap.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    interval = 1.0 / args.rate
    total = int(args.rate * args.minutes * 60)
    start = time.perf_counter()

    print(f"Broadcasting {total} packets at {args.rate} Hz "
          f"for {args.minutes} min on port {args.port}")
    print(f"Session label: {args.session}")
    print("Start the receivers FIRST, then leave this running. Ctrl+C to stop early.")

    seq = 0
    try:
        while seq < total:
            target = start + seq * interval
            now = time.perf_counter()
            if now < target:
                time.sleep(target - now)
            pkt = json.dumps({
                "seq": seq,
                "t_send": time.time(),      # wall clock, only for reference
                "session": args.session,
            }).encode("utf-8")
            sock.sendto(pkt, ("255.255.255.255", args.port))
            if seq % (int(args.rate) * 30) == 0:   # progress every ~30 s
                elapsed = (time.perf_counter() - start) / 60.0
                print(f"  seq={seq}  elapsed={elapsed:.1f} min")
            seq += 1
    except KeyboardInterrupt:
        print(f"\nStopped early at seq={seq}")

    sock.close()
    print(f"\nDone. Sent {seq} packets (last seq = {seq-1}).")
    print(f"Tell the analysis script this run sent {seq} packets.")

if __name__ == "__main__":
    main()
