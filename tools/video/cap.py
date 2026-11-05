"""Capture one macOS window as timestamped JPEG frames until <dir>/STOP exists.  usage: cap.py DIR WINDOW_ID"""
import os, subprocess, sys, time
d, wid = sys.argv[1], sys.argv[2]
os.makedirs(d, exist_ok=True)
t0 = time.time()
while not os.path.exists(os.path.join(d, "STOP")):
    ms = int((time.time() - t0) * 1000)
    subprocess.run(["screencapture", "-x", "-o", "-t", "jpg", f"-l{wid}", f"{d}/f_{ms:08d}.jpg"])
