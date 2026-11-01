# sim_v2.py - corrected dependability model (replaces run_episode.py for all results).
#
# Fixes vs v1:
#  1. Misclassification is SHARED: one camera, one classifier, one broadcast. The STOP hold
#     is read once (from the measured per-hold STOP misread probability) and every robot
#     receives the same command.
#  2. The operator laptop REBROADCASTS the current command at RATE_HZ (RAIST: >30 Hz).
#     Robots latch the last command they received (RAIST behaviour).
#  3. Packet loss follows a Gilbert-Elliott two-state channel (bursty Wi-Fi loss), parameterised
#     by mean loss rate and mean burst duration. Each robot has its own channel; a fraction
#     `common` of bursts is shared by all robots (router-side outage) via one extra common chain.
#
# Safety requirement (unchanged): after the operator's true STOP, every robot is at rest within
# T_STOP. A robot violates it if it is still moving at the deadline.
import numpy as np
from robot import Robot, V_MAX, A_MAX
from safety import T_STOP, V_STOPPED

DT = 0.02
RATE_HZ = 30.0

class GilbertElliott:
    """Two-state Markov loss channel, one step per broadcast packet.
    mean_loss = stationary P(lost); mean_burst_s = mean duration of a loss burst (BAD state).
    Simple Gilbert model: GOOD -> packet delivered, BAD -> packet lost."""
    def __init__(self, mean_loss, mean_burst_s, rng, rate_hz=RATE_HZ):
        self.rng = rng
        if mean_loss <= 0:
            self.p_gb, self.p_bg = 0.0, 1.0
        else:
            burst_pkts = max(1.0, mean_burst_s * rate_hz)
            self.p_bg = 1.0 / burst_pkts                       # mean burst = 1/p_bg packets
            self.p_gb = self.p_bg * mean_loss / (1 - mean_loss) # stationary loss = p_gb/(p_gb+p_bg)
        self.bad = rng.random() < (self.p_gb / (self.p_gb + self.p_bg) if mean_loss > 0 else 0)
    def step(self):
        if self.bad:
            if self.rng.random() < self.p_bg: self.bad = False
        else:
            if self.rng.random() < self.p_gb: self.bad = True
        return self.bad   # True = packet lost


def run_episode_v2(N, mean_loss, mean_burst_s, seed, p_misread, common=0.0,
                   rec_delay_s=0.033, t_stop_cmd=1.0, timeout_s=None, issue_stop=True, sim_s=3.0):
    """Returns dict(violated, n_moving, misread, nuisance_stops).
    timeout_s: None = RAIST latching only; else fail-safe stop when no packet for timeout_s.
    issue_stop=False: no STOP is ever given (measures nuisance stops of the fail-safe)."""
    rng = np.random.default_rng(seed)
    robots = [Robot(x=i * 3.0, y=0.0, theta=0.0, robot_id=i) for i in range(N)]
    own = [GilbertElliott(mean_loss * (1 - common), mean_burst_s, rng) for _ in range(N)]
    shared = GilbertElliott(mean_loss * common, mean_burst_s, rng)
    misread = issue_stop and (np.random.default_rng([seed, 7]).random() < p_misread)  # ONE draw, whole swarm
    t_emit = t_stop_cmd + rec_delay_s                         # when the recogniser outputs STOP
    latched = ["DRIVE"] * N
    last_rx = [0.0] * N
    failsafe = [False] * N
    deadline = t_stop_cmd + T_STOP
    v_after = [0.0] * N
    next_tx, t = 0.0, 0.0
    while t < sim_s:
        if t >= next_tx - 1e-9:
            cmd = "STOP" if (issue_stop and t >= t_emit and not misread) else "DRIVE"
            common_lost = shared.step()
            for i in range(N):
                lost = own[i].step() or common_lost
                if not lost:
                    last_rx[i] = t
                    if latched[i] != "STOP":   # STOP latches until explicit resume
                        latched[i] = cmd
            next_tx += 1.0 / RATE_HZ
        for i, r in enumerate(robots):
            if timeout_s is not None and t - last_rx[i] > timeout_s:
                failsafe[i] = True
            stop = latched[i] == "STOP" or failsafe[i]
            r.step(0.0 if stop else V_MAX, 0.0, DT)
            if t >= deadline:
                v_after[i] = max(v_after[i], abs(r.v))
        t += DT
    n_moving = sum(v > V_STOPPED for v in v_after)
    return {"violated": issue_stop and n_moving > 0, "n_moving": n_moving if issue_stop else 0,
            "misread": misread, "nuisance_stops": sum(failsafe) if not issue_stop else 0}


def analytic_violation(N, mean_loss, mean_burst_s, p_misread, rec_delay_s=0.033, common=0.0,
                       t_stop_cmd=1.0):
    """Closed form for independent channels (common=0). A robot violates iff every broadcast
    between the recogniser's STOP output and the last moment it can still brake in time is lost.
    Timing matches the simulator: broadcasts on a 1/RATE_HZ grid, speed checked from the
    deadline step onward, 'stopped' means speed <= V_STOPPED."""
    t_emit = t_stop_cmd + rec_delay_s
    t_last = t_stop_cmd + T_STOP + DT - (V_MAX - V_STOPPED) / A_MAX
    first = int(np.ceil(t_emit * RATE_HZ - 1e-9)); last = int(np.floor(t_last * RATE_HZ + 1e-9))
    k = max(0, last - first + 1)                       # broadcasts inside the slack window
    if mean_loss <= 0 or k == 0:
        q = 0.0 if k else 1.0
    else:
        p_bg = 1.0 / max(1.0, mean_burst_s * RATE_HZ)
        q = mean_loss * (1 - p_bg) ** (k - 1)         # start lost, stay lost k-1 more steps
    return p_misread + (1 - p_misread) * (1 - (1 - q) ** N), k, q


def run_episode_relay(N, mean_loss, mean_burst_s, seed, p_misread, rx_fraction=0.0,
                      spacing_m=3.0, relay_range_m=6.0, rec_delay_s=0.033,
                      t_stop_cmd=1.0, relay=True, sim_s=3.0):
    """Peer relay of STOP. Every robot that has latched STOP rebroadcasts it at RATE_HZ to robots
    within relay_range_m (multi-hop: relayed robots relay too).
    Where do loss bursts happen? rx_fraction splits the burst loss between
      - the robot's own receiver (deaf to everyone: operator AND neighbours), loss = mean_loss*rx_fraction
      - individual links (operator->i, j->i, each its own burst channel), loss = mean_loss*(1-rx_fraction).
    rx_fraction=0: pure path fading (relay can route around it). rx_fraction=1: pure receiver deafness
    (relay cannot help). Same scenario, timing, shared misread and safety check as run_episode_v2.
    relay=False gives plain 30 Hz broadcast. Relay airtime/collisions are not modelled (limitation)."""
    rng = np.random.default_rng(seed)
    robots = [Robot(x=i * spacing_m, y=0.0, theta=0.0, robot_id=i) for i in range(N)]
    nbrs = [set(j for j in range(N) if j != i and abs(i - j) * spacing_m <= relay_range_m) for i in range(N)]
    rx = [GilbertElliott(mean_loss * rx_fraction, mean_burst_s, rng) for _ in range(N)]
    op = [GilbertElliott(mean_loss * (1 - rx_fraction), mean_burst_s, rng) for _ in range(N)]
    links = {}
    def link(j, i):
        if (j, i) not in links: links[(j, i)] = GilbertElliott(mean_loss * (1 - rx_fraction), mean_burst_s, rng)
        return links[(j, i)]
    misread = np.random.default_rng([seed, 7]).random() < p_misread
    t_emit = t_stop_cmd + rec_delay_s
    stopped = [False] * N
    deadline = t_stop_cmd + T_STOP
    v_after = [0.0] * N
    next_tx, t = 0.0, 0.0
    while t < sim_s:
        if t >= next_tx - 1e-9:
            op_stop = t >= t_emit and not misread
            deaf = [ch.step() for ch in rx]
            op_lost = [ch.step() for ch in op]
            senders = [j for j in range(N) if stopped[j]] if relay else []
            new = []
            for i in range(N):
                if stopped[i]: continue
                got = op_stop and not (deaf[i] or op_lost[i])
                if not got and not deaf[i]:
                    for j in senders:
                        if j in nbrs[i] and not link(j, i).step():
                            got = True; break
                if got: new.append(i)
            for i in new: stopped[i] = True
            next_tx += 1.0 / RATE_HZ
        for i, r in enumerate(robots):
            r.step(0.0 if stopped[i] else V_MAX, 0.0, DT)
            if t >= deadline: v_after[i] = max(v_after[i], abs(r.v))
        t += DT
    n_moving = sum(v > V_STOPPED for v in v_after)
    return {"violated": n_moving > 0, "n_moving": n_moving, "misread": misread}
