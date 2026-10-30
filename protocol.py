# protocol.py
# Defines the command packet format sent over UDP from operator to robots.
# Each packet carries a send-timestamp so robots can measure real latency.

import json
import time

# UDP settings
UDP_IP = "127.0.0.1"      # localhost: real network stack, no external traffic
UDP_PORT = 5005           # any free port
BUFFER_SIZE = 1024

# Valid commands (map to your formations + STOP)
COMMANDS = ["CIRCLE", "LINE", "CLUSTER", "SPLIT", "STOP", "WAIT"]

def make_packet(command, seq):
    """Build a command packet with a high-resolution send timestamp."""
    assert command in COMMANDS, f"unknown command {command}"
    packet = {
        "command": command,
        "seq": seq,                      # sequence number, to detect drops later
        "t_send": time.perf_counter(),   # monotonic clock, seconds, high-res
    }
    return json.dumps(packet).encode("utf-8")

def parse_packet(data):
    """Decode a received packet back into a dict."""
    return json.loads(data.decode("utf-8"))