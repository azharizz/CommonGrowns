"""Crop each captured frame to the chat pane, shrink it, delete the 4 MB original.  usage: sweep.py DIR"""
import glob, os, sys, time
from PIL import Image
CROP = (1468, 192, 1468 + 1416, 192 + 1926)
d = sys.argv[1]; out = os.path.join(d, "small"); os.makedirs(out, exist_ok=True)
while True:
    frames = sorted(glob.glob(os.path.join(d, "f_*.jpg")))
    done = os.path.exists(os.path.join(d, "STOP"))
    ready = [f for f in frames if time.time() - os.path.getmtime(f) > 0.6]
    if not ready and (done and not frames):
        break
    for f in (ready if not done else frames):
        try:
            im = Image.open(f).crop(CROP).resize((780, 1060), Image.LANCZOS)
            im.save(os.path.join(out, os.path.basename(f)), quality=88)
            os.remove(f)
        except Exception:
            time.sleep(0.2)
    time.sleep(0.3)
