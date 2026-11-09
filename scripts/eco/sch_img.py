import subprocess
from PIL import Image, ImageDraw, ImageFont
Z = 10 / 3.7795; T = "/tmp/claude-0/-home-claude/b07cc2f1-81b1-5c9b-bc59-c1d915939636/scratchpad/"
def ren(svg, out): subprocess.run(["rsvg-convert", "-z", str(Z), "-b", "white", svg, "-o", T + out], check=True)
ren("sch/svg_orig/ecp5-mini-FPGA Config.svg", "cfg_b.png"); ren("sch_eco/svg/ecp5-mini-FPGA Config.svg", "cfg_a.png")
ren("sch_eco/svg/ecp5-mini.svg", "root_a.png"); ren("sch_eco/svg/ecp5-mini-LEDs.svg", "leds_a.png")
def crop(f, x0, y0, x1, y1): return Image.open(T + f).crop((int(x0 * 10), int(y0 * 10), int(x1 * 10), int(y1 * 10)))
B = lambda n: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", n)
rows = [[("JTAG before: 6-pin header J2", crop("cfg_b.png", 8, 93, 72, 124)), ("JTAG after: TC2050 pads J2 (ARM 10-pin)", crop("cfg_a.png", 8, 93, 72, 124))],
        [("New: Qwiic J6 + 4k7 pull-ups (root sheet)", crop("root_a.png", 248, 58, 312, 92))],
        [("LEDs: D9–D11 marked DNP / not on board", crop("leds_a.png", 75, 70, 250, 125))]]
W = max(sum(t[1].width + 20 for t in r) + 20 for r in rows); H = 90 + sum(max(t[1].height for t in r) + 60 for r in rows)
img = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(img)
d.text((20, 20), "ECP5 Mini Rev 1.1, schematic changes (parity with the PCB: 0 new mismatches)", fill="black", font=B(26))
y = 80
for r in rows:
    x = 20
    for title, im in r:
        d.text((x, y), title, fill=(20, 60, 140), font=B(20)); img.paste(im, (x, y + 32)); d.rectangle((x, y + 32, x + im.width, y + 32 + im.height), outline=(180, 180, 180)); x += im.width + 20
    y += max(t[1].height for t in r) + 60
img.save("/home/claude/route/eco_schematic_changes.png"); print(img.size)
