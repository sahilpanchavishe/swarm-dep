# FULL GUIDE - Wi-Fi measurement (start to end)

WHY NOTHING ARRIVED: packets from one laptop to another are blocked somewhere (usually the router's
"client/AP isolation", or a firewall). Guessing wastes hours, so this kit has netcheck.py, which tells
you in 1 minute exactly what is blocked. Do NOT start the 10-minute sessions until netcheck says PASS.

## 1. Files (one zip: wifi_kit_final.zip)  -> unzip on EVERY laptop
Mac: double-click it (folder swarm-dep appears in Downloads). Windows: right-click > Extract All.
Inside swarm-dep: wifi/ (wifi_rx.py, wifi_tx.py, netcheck.py, fit_wifi.py), record_stop.py, this guide.
Python needed (check): Mac `python3 --version`  Windows `py --version`  (install 3.11/3.12 from python.org,
tick "Add Python to PATH" on Windows, if missing). The Wi-Fi scripts need nothing else.

## 2. Prepare every laptop
 - All on the SAME Wi-Fi network (not Ethernet). VPN off. Plugged into power. Sleep off.
 - Windows: set the Wi-Fi network to PRIVATE (Settings > Network & Internet > Wi-Fi > click the network > Private).
 - Windows: open cmd as Administrator and run once:
   netsh advfirewall firewall add rule name="swarm-udp" dir=in action=allow protocol=UDP localport=5006-5007 profile=any
 - Mac: nothing, click Allow if asked about incoming connections.
 - Open a terminal in the folder:  Mac: cd ~/Downloads/swarm-dep   Windows: cd %USERPROFILE%\Downloads\swarm-dep
   (if you extracted into a "measurement_kit" or "wifi_kit_final" folder, cd into that and then into swarm-dep)
 - Find each laptop's IP:  Mac: ipconfig getifaddr en0 (or en1)   Windows: ipconfig  -> IPv4 Address under Wi-Fi.
   Write them all on paper. The first three numbers must match on every laptop (e.g. 192.168.1.x).
   If they don't match, the laptops are on different networks - reconnect them to the same Wi-Fi.

## 3. THE CHECK (netcheck) - 1 minute
 On every RECEIVER:   Mac: python3 wifi/netcheck.py listen      Windows: py wifi\netcheck.py listen
 On the SENDER:       Mac: python3 wifi/netcheck.py probe --to R1IP,R2IP,R3IP
                      Windows: py wifi\netcheck.py probe --to R1IP,R2IP,R3IP
 (use the real receiver IPs, comma-separated, no spaces)
 Receiver screens must show lines "GOT ... from <sender IP>". The sender prints PASS/FAIL per receiver.

## 4. If netcheck says FAIL (do these in order, rerun netcheck after each)
 a) Receiver shows NO "GOT" lines  => packets never arrive.
    1. Check IPs share the first three numbers (section 2).
    2. Windows receiver: turn the firewall OFF for the test: Windows Security > Firewall & network protection >
       click your Wi-Fi network > Microsoft Defender Firewall > Off. (Turn it on again afterwards.)
    3. Still nothing => ROUTER ISOLATION. Log into the router (browser: 192.168.0.1 or 192.168.1.1; login is on its sticker)
       > Wireless/Wi-Fi/Advanced > turn OFF "AP Isolation / Client Isolation / Wireless Isolation" > Save.
       College/shared/guest Wi-Fi and most phone hotspots always isolate: they CANNOT work.
    4. If you cannot change the router, make your own network (below).
 b) Receiver shows "GOT" lines but sender says 0 echoes => the SENDER's firewall blocks replies. Turn the sender's
    firewall off for the test (or run the netsh command above on the sender).
 c) Unicast PASS but BROADCAST FAIL => fine, continue using  --dest  mode (section 5). Note it in the paper as a lower bound.

 MAKE YOUR OWN NETWORK (if the router can't be changed): use a spare Windows laptop that is NOT sender or receiver:
 Settings > Network & Internet > Mobile hotspot > On > Properties > Edit > band 2.4 GHz. Join all measurement laptops to it.
 Redo section 2 (IPs change) and section 3. Write in notes.txt that this network was used.

## 5. Measurement (ONLY after netcheck PASS)
 Test first (30 s). Receivers first, with different names:
   Mac: python3 wifi/wifi_rx.py --name R1        Windows: py wifi\wifi_rx.py --name R1
 Then sender (broadcast if broadcast PASSED; otherwise add --dest with receiver IPs):
   Mac: python3 wifi/wifi_tx.py --minutes 0.5 --label test [--dest R1IP,R2IP,R3IP]
   Windows: py wifi\wifi_tx.py --minutes 0.5 --label test [--dest R1IP,R2IP,R3IP]
 Each receiver prints FIRST PACKET and counts up. At "done" press Ctrl+C (Windows: Ctrl+Break if stuck).
 Delete test files:  Mac: rm rx_*.csv    Windows: del rx_*.csv
 Real sessions (10 min each; receivers first, then sender; same commands with --minutes 10):
   1 quiet room  --label lab_quiet   then  Mac: mkdir session1_quiet && mv rx_*.csv session1_quiet/
                                          Windows: mkdir session1_quiet && move rx_*.csv session1_quiet\
   2 busy room (many phones/laptops streaming)  --label lab_busy  -> folder session2_busy
   3 far / behind wall (R3,R4 far; R1,R2 side by side) --label far_wall -> folder session3_far
 Don't redo sessions to improve numbers. Low loss is a valid result.

## 6. Send back
 Attach to the Claude chat: every .csv in session1_quiet, session2_busy, session3_far (say which laptop = R1/R2/R3),
 plus notes.txt (router model or hotspot, laptop positions/distances, number of devices connected, time of day),
 plus a copy of the netcheck output (which showed PASS/FAIL). Then I run the analysis.

## 7. STOP-dataset recording is separate: see RUN_ME.md from the first kit (record_stop.py is included here too).

## 8. SENDER LAPTOP IS THE HOTSPOT (no router) - Windows sender
 Why it failed before: a hotspot host has TWO networks (the internet one and the hotspot one, 192.168.137.x). The
 old scripts picked the wrong one. Now always pass  --src 192.168.137.1  (the host's address on its own hotspot).
 1. Sender: Settings > Network & Internet > Mobile hotspot > Share over: Wi-Fi > Edit: name, password,
    Network band: 2.4 GHz > Save > turn Mobile hotspot ON. (If it says it needs an internet connection, connect the
    laptop to any Wi-Fi/Ethernet or USB-tether a phone first.)
 2. Receivers: join that hotspot's Wi-Fi name. Receiver IPs will be 192.168.137.x (check with ipconfig / ipconfig getifaddr en0).
 3. Sender IP on the hotspot: ipconfig -> the adapter "Local Area Connection* N" -> IPv4 192.168.137.1.
 4. Run the firewall command (section 2) on sender AND receivers.
 5. Check (receivers: listen as before). Sender:
      py wifi\netcheck.py probe --to 192.168.137.2,192.168.137.3 --src 192.168.137.1
 6. Measurement. Sender:
      py wifi\wifi_tx.py --minutes 10 --label lab_quiet --src 192.168.137.1 --dest 192.168.137.255
    (if broadcast fails but netcheck unicast passes:  --dest 192.168.137.2,192.168.137.3 )
 Receivers' commands are unchanged. Write in notes.txt: "sender-hosted Windows Mobile Hotspot, 2.4 GHz, channel auto".
