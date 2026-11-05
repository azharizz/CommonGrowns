"""Turn captured frames into a 1080p scene clip: compress idle waits, crop the chat pane, add a caption panel.
usage: build.py FRAMES_DIR OUT.mp4 'Title' 'bullet 1|bullet 2|bullet 3' 'step label'"""
import glob, os, subprocess, sys
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat

CROP = (1468, 192, 1416, 1926)       # x, y, w, h in the 3600x2252 window frames (chat pane only: no chat list, no browser UI)
W, H = 1920, 1080
BOLD, REG = ("/System/Library/Fonts/Helvetica.ttc", 1), ("/System/Library/Fonts/Helvetica.ttc", 0)
def font(spec, n): return ImageFont.truetype(spec[0], n, index=spec[1])

def background(title, bullets, step, path):
    im = Image.new("RGB", (W, H), "#0f1b2d"); d = ImageDraw.Draw(im)
    for y in range(H):  # soft vertical gradient
        c = int(15 + 18 * y / H); d.line((0, y, W, y), fill=(c, 27 + c // 3, 45 + c // 2))
    d.rounded_rectangle((70, 70, 940, 150), radius=14, fill="#1f7ae0")
    d.text((100, 88), "CommonGrown", font=font(BOLD, 44), fill="white")
    d.text((100, 230), step.upper(), font=font(BOLD, 26), fill="#7fb4ff")
    y = 280
    for line in wrap(d, title, font(BOLD, 62), 800):
        d.text((100, y), line, font=font(BOLD, 62), fill="white"); y += 76
    y += 30
    for b in bullets:
        lines = wrap(d, b, font(REG, 34), 780)
        d.ellipse((100, y + 14, 116, y + 30), fill="#7fb4ff")
        for line in lines:
            d.text((140, y), line, font=font(REG, 34), fill="#dbe7f7"); y += 46
        y += 22
    d.text((100, H - 80), "Built on Switch  |  consent-first B2B matching", font=font(REG, 26), fill="#6f87a8")
    im.save(path)

def wrap(d, text, f, width):
    out, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if d.textlength(trial, font=f) <= width: line = trial
        else: out.append(line); line = word
    return out + [line]

def timeline(frames):
    """(path, seconds) per kept frame; static runs longer than 8s are compressed."""
    def small(p):
        im = Image.open(p); im.draft("L", (195, 265)); return im.convert("L").resize((60, 82))
    ts = [int(os.path.basename(p)[2:10]) / 1000 for p in frames]
    kept, prev, run_start = [], None, 0
    for i, p in enumerate(frames):
        cur = small(p)
        moved = prev is None or ImageStat.Stat(ImageChops.difference(cur, prev)).mean[0] > 0.35
        if moved:
            kept.append([p, ts[i], ts[i]]); 
        else:
            kept[-1][2] = ts[i]
        prev = cur
    out = []
    for n, (p, a, b) in enumerate(kept):
        end = kept[n + 1][1] if n + 1 < len(kept) else b + 1.5
        span = end - a
        out.append((p, span if span <= 8 else 3 + min(4, (span - 3) / 10)))
    return out

def main(frames_dir, out, title, bullets, step):
    frames_dir, out = os.path.abspath(frames_dir), os.path.abspath(out)
    frames = sorted(glob.glob(os.path.join(frames_dir, "small", "f_*.jpg")))
    plan = timeline(frames)
    bg = os.path.join(frames_dir, "bg.png"); background(title, bullets.split("|"), step, bg)
    lst = os.path.join(frames_dir, "list.txt")
    with open(lst, "w") as f:
        for p, s in plan: f.write(f"file '{p}'\nduration {s:.3f}\n")
        f.write(f"file '{plan[-1][0]}'\n")
    total = sum(s for _, s in plan)
    x, y, w, h = CROP
    vf = "[1:v]scale=-2:1000[c];[0:v][c]overlay=1090:40,fps=30,format=yuv420p"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-t", f"{total:.2f}", "-i", bg, "-f", "concat", "-safe", "0", "-i", lst,
                    "-filter_complex", vf, "-t", f"{total:.2f}", "-c:v", "libx264", "-crf", "20", "-preset", "medium", out], check=True)
    print(f"{os.path.basename(out)}: {len(frames)} frames, {total:.0f}s after compressing waits")

if __name__ == "__main__":
    main(*sys.argv[1:6])
