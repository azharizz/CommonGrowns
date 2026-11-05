"""Build every scene clip, the intro/outro cards and the final MP4.  usage: make_video.py REC_DIR OUT.mp4"""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import build

rec, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
SCENES = [
 ("s1", "Scene 1 of 6", "Acme Events: a summit organizer needs sponsors",
  "Employees just chat. No commands, no forms.|The bot notices the need and asks the owner before doing anything.|The internal 40k floor stays private, and the 5,000 vs 6,000 disagreement is flagged for the owner."),
 ("s2", "Scene 2 of 6", "CloudKita: a cloud provider wants exposure",
  "Public budget range is shared. The internal 90k ceiling is not.|Top match: Acme Events. NimbusID is correctly a no-match: both are sponsors.|With 0 credits the paid brief is locked. Match headlines stay free."),
 ("s3", "Scene 3 of 6", "PromptWorks: an AI agency wants implementation work",
  "Same flow, a different role in the network.|It matches CloudKita's implementation-partner opportunity.|The rate card stays confidential."),
 ("s4", "Scene 4 of 6", "SecureNusa: a security vendor wants CISO leads",
  "An honest result: only a weak fit with Acme until CISO attendance is proven.|The 25k minimum tier stays internal."),
 ("s5", "Scene 5 of 6", "BatikMesin: a machine supplier looks for distributors",
  "A different industry and region entirely.|Matches SiamPack Distribution across Thailand and Vietnam.|Sponsor companies are correctly ruled out."),
 ("s6", "Scene 6 of 6", "Paying for depth: a full brief",
  "Acme has credits and receives a full brief: fits, risks, unknowns, next step.|Each brief costs 1 credit. Headlines are free.|All output is advice for humans to review, not an agreement."),
]
W, H = 1920, 1080

def card(path, headline, lines, footer):
    im = Image.new("RGB", (W, H), "#0f1b2d"); d = ImageDraw.Draw(im)
    for y in range(H):
        c = int(15 + 18 * y / H); d.line((0, y, W, y), fill=(c, 27 + c // 3, 45 + c // 2))
    d.rounded_rectangle((120, 150, 760, 240), radius=16, fill="#1f7ae0")
    d.text((150, 168), "CommonGrown", font=build.font(build.BOLD, 54), fill="white")
    y = 320
    for l in build.wrap(d, headline, build.font(build.BOLD, 76), 1500):
        d.text((120, y), l, font=build.font(build.BOLD, 76), fill="white"); y += 94
    y += 40
    for l in lines:
        for part in build.wrap(d, l, build.font(build.REG, 40), 1500):
            d.text((120, y), part, font=build.font(build.REG, 40), fill="#dbe7f7"); y += 54
        y += 14
    d.text((120, H - 100), footer, font=build.font(build.REG, 30), fill="#6f87a8")
    im.save(path)

def still(png, mp4, seconds):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-t", str(seconds), "-i", png,
                    "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "20", "-preset", "medium", mp4], check=True)

os.makedirs(os.path.join(rec, "clips"), exist_ok=True)
card(os.path.join(rec, "intro.png"), "Add a bot to your company chat.",
     ["It listens to how your team talks, keeps a short summary of what you need and offer,",
      "and finds companies worth meeting. Humans approve everything and close the deal."],
     "Flip the Switch hackathon  |  built on Switch  |  all companies and chats shown are fictional")
card(os.path.join(rec, "outro.png"), "Discovery and prep by AI. The deal stays human.",
     ["Consent first: nothing is published without the owner's yes.",
      "Confidential numbers stay private. Chats are summarized, then deleted.",
      "github.com/azharizz/CommonGrowns"],
     "Flip the Switch hackathon  |  built on Switch")
still(os.path.join(rec, "intro.png"), os.path.join(rec, "clips", "00_intro.mp4"), 6)
still(os.path.join(rec, "outro.png"), os.path.join(rec, "clips", "99_outro.mp4"), 7)

def one(scene):
    key, step, title, bullets = scene
    build.main(os.path.join(rec, key), os.path.join(rec, "clips", f"{key}.mp4"), title, bullets, step)
with ThreadPoolExecutor(3) as pool:
    list(pool.map(one, SCENES))

def join(names, target):
    lst = os.path.join(rec, "clips", "list_" + os.path.basename(target) + ".txt")
    open(lst, "w").write("".join(f"file '{os.path.join(rec, 'clips', n)}'\n" for n in names))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    "-movflags", "+faststart", target], check=True)
    print("FINAL", target)

join(["00_intro.mp4"] + [f"{k}.mp4" for k, *_ in SCENES] + ["99_outro.mp4"], out)
join(["00_intro.mp4", "s1.mp4", "s2.mp4", "s6.mp4", "99_outro.mp4"], out.replace(".mp4", "_short.mp4"))
