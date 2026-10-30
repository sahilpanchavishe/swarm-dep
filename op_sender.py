# operator.py
# Broadcasts gesture commands over UDP, timestamped.
# Run this in its own terminal AFTER the robots are listening.

import socket
import time
from protocol import UDP_IP, UDP_PORT, make_packet

# A scripted command timeline: (time_in_seconds, command)
# This stands in for the human operator's gestures for now.
SCHEDULE = [
    (0.0, "CIRCLE"),
    (8.0, "LINE"),
    (16.0, "STOP"),    # the safety-critical one
    (20.0, "CLUSTER"),
]

def main():
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   # UDP
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)   # UDP
    start = time.perf_counter()
    seq = 0
    print("Operator broadcasting. Commands:")
    for t_cmd, command in SCHEDULE:
        # wait until this command's scheduled time
        while time.perf_counter() - start < t_cmd:
            time.sleep(0.001)
        packet = make_packet(command, seq)
        sock.sendto(packet, ("255.255.255.255", UDP_PORT))
        print(f"  t={t_cmd:5.1f}s  seq={seq}  {command}")
        seq += 1
    # Keep sending the last command periodically so late-joining robots hold state
    # (optional; omit for now)
    sock.close()

if __name__ == "__main__":
    main()