# wifi_receiver.py
# Logs every packet that arrives from the sender. Run ONE copy on EACH
# receiver device, placed where a robot would stand. No clock sync needed:
# we only record which sequence numbers arrived, so loss and burst length
# are measured from the gaps in the sequence, not from cross-machine timing.
#
# Usage (give each device a different id: r0, r1, r2, ...):
#   python3 wifi_receiver.py --id r0 --port 5005
#
# Start the receivers BEFORE the sender. Press Ctrl+C when the sender finishes.
# Output: data/wifi/received_<id>.csv  with columns seq,t_recv

import socket
import time
import os
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, help="unique receiver id, e.g. r0")
    ap.add_argument("--port", type=int, default=5005)
    args = ap.parse_args()

    import json
    os.makedirs("data/wifi", exist_ok=True)
    out = f"data/wifi/received_{args.id}.csv"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except (AttributeError, OSError):
        pass
    sock.bind(("", args.port))

    print(f"Receiver {args.id} listening on port {args.port}")
    print(f"Logging to {out}. Press Ctrl+C when the sender is done.")

    rows = []
    last_report = time.perf_counter()
    try:
        while True:
            data, _ = sock.recvfrom(2048)
            t_recv = time.perf_counter()
            try:
                pkt = json.loads(data.decode("utf-8"))
                seq = pkt["seq"]
            except (ValueError, KeyError):
                continue
            rows.append((seq, t_recv))
            if time.perf_counter() - last_report > 30:
                print(f"  {args.id}: {len(rows)} packets received so far")
                last_report = time.perf_counter()
    except KeyboardInterrupt:
        pass

    with open(out, "w") as f:
        f.write("seq,t_recv\n")
        for seq, t in rows:
            f.write(f"{seq},{t:.6f}\n")
    print(f"\nReceiver {args.id} done. Logged {len(rows)} packets to {out}")

if __name__ == "__main__":
    main()
