# Measuring the real Wi-Fi channel (the number the headline depends on)

The corrected model shows that 30 Hz rebroadcast defeats short drops; only long loss bursts make
robots miss the STOP. So the paper needs the burst statistics of a real 2.4 GHz network.

Setup: the router you would use with the robots; one sender laptop; 2-4 receiver laptops placed
where robots would be (spread out, some far / behind a wall). All on the same Wi-Fi.

1. On each receiver:  `python wifi/wifi_rx.py --name R1`   (R2, R3 ...)
2. On the sender:     `python wifi/wifi_tx.py --minutes 10 --label lab_idle`
   (if receivers get nothing, pass `--dest 192.168.x.255`, your subnet's broadcast address)
3. When the sender prints done, Ctrl+C every receiver. Collect the rx_*.csv files.
4. `python wifi/fit_wifi.py wifi/rx_*.csv` -> loss rate, burst lengths, tail, overlap.

Do at least three 10-minute sessions: quiet lab, busy time (many phones/laptops), and far/through a
wall. That gives a measured low/typical/bad channel instead of an assumed one.
Note: literature reports Wi-Fi bursts are heavy-tailed (rare very long outages); the tail counts
in the output are what matter for STOP safety.
