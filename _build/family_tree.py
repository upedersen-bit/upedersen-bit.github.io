"""Family tree for the Introduction, redrawn so that Karen Steffansdatter stands beside her husband Jens Sørensen."""
import sys
from html import escape

W = 2270
BOX = 410
COL = [20 + i * 450 for i in range(5)]          # left edges of five columns
INK, LINE, MUTED = "#111", "#444", "#555"
out = []

def box(x, y, w, h, lines, kind="plain"):
    fill, stroke, dash, sw = "#fff", "#333", "", 2.5
    if kind == "main":
        fill, stroke, sw = "#f1ebe0", "#5a4a32", 3.5
    if kind == "foster":
        fill, stroke, dash = "#f6f6f6", "#999", ' stroke-dasharray="10 7"'
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')
    names = [l for l in lines if l[0] == "b"]
    subs = [l for l in lines if l[0] == "s"]
    n = len(names) + len(subs)
    total = len(names) * 46 + len(subs) * 47
    ty = y + (h - total) / 2 + 36
    cx = x + w / 2
    for _, t in names:
        out.append(f'<text x="{cx}" y="{ty}" text-anchor="middle" font-weight="700" font-size="38" fill="{INK}">{escape(t)}</text>')
        ty += 46
    for _, t in subs:
        out.append(f'<text x="{cx}" y="{ty + 1}" text-anchor="middle" font-size="31" fill="#333">{escape(t)}</text>')
        ty += 47

def line(x1, y1, x2, y2, dash=False):
    d = ' stroke-dasharray="10 8" stroke="#999"' if dash else f' stroke="{LINE}"'
    out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"{d} stroke-width="3"/>')

def label(x, y, t, anchor="start"):
    out.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-style="italic" font-size="30" fill="{MUTED}">{escape(t)}</text>')

# row 1: the two older couples
box(COL[0], 20, BOX, 180, [("b", "Ole Nielsen"), ("b", '"Nordmand"'), ("s", "b. c. 1784; d. 1836?")])
box(COL[1], 20, BOX, 132, [("b", "Maren Jensdatter"), ("s", "b. c. 1783")])
line(COL[0] + BOX, 90, COL[1], 90)
box(COL[3], 20, BOX, 180, [("b", "Stephan"), ("b", "Christensen"), ("s", "c. 1756–1820")])
box(COL[4], 20, BOX, 180, [("b", "Kirsten"), ("b", "Andersdatter"), ("s", "c. 1750–1823")])
line(COL[3] + BOX, 90, COL[4], 90)

# Ole and Maren -> Niels Christian
xa = COL[0] + BOX + 20                      # 450, between Ole and Maren
line(xa, 90, xa, 880)
label(xa + 16, 240, "m. 1821")

# Stephan and Kirsten -> Karen and Anders
xs = COL[3] + BOX + 20                       # between Stephan and Kirsten
line(xs, 90, xs, 280)
ck, ca = COL[3] + BOX / 2, COL[4] + BOX / 2
line(ck, 280, ca, 280)
line(ck, 280, ck, 320)
line(ca, 280, ca, 320)

# row 2: foster parents; Jens Sørensen married to Karen; her brother Anders
box(COL[0], 320, BOX, 180, [("b", "Christen Nielsen &"), ("b", "Karen Nielsdatter"), ("s", "foster parents, Skelund")], "foster")
box(COL[2], 344, BOX, 132, [("b", "Jens Sørensen"), ("s", "farmer; d. 1865")])
box(COL[3], 320, BOX, 180, [("b", "Karen"), ("b", "Steffansdatter"), ("s", "d. 1877")])
box(COL[4], 320, BOX, 180, [("b", "Anders"), ("b", "Stephansen"), ("s", "1791–1870")])
xm = COL[2] + BOX + 20                       # between Jens and Karen
line(COL[2] + BOX, 410, COL[3], 410)
line(xm, 410, xm, 880)
label(xm, 398, "m.", "middle")

# row 3: Niels Christian married to Kirsten Marie
line(COL[0] + 205, 500, COL[0] + 205, 880, dash=True)
nx, nw = 170, 580
box(nx, 880, nw, 180, [("b", "Niels Christian Olesen"), ("b", "(Damborg)"), ("s", '1821–1899 · "Nelse C. Olson"')], "main")
kx = xm - BOX / 2
box(kx, 880, BOX, 180, [("b", "Kirsten Marie"), ("b", "Jensen"), ("s", "1825–1874")])
line(nx + nw, 960, kx, 960)
xc = (nx + nw + kx) / 2
label(xc, 930, "m. 1854", "middle")

# Mary
line(nx + nw / 2, 1060, nx + nw / 2, 1240)
label(nx + nw / 2 + 20, 1190, "m. 1871, Blair, Nebraska")
box(nx, 1240, nw, 132, [("b", "Mary (Caren) Nelsen"), ("s", "b. c. 1830–36, Kongsberg; d. 1917?")])

# children of Niels Christian and Kirsten Marie
line(xc, 960, xc, 1520)
cc = [COL[i] + BOX / 2 for i in range(4)]
line(cc[0], 1520, cc[3], 1520)
kids = [("Anders Christian", "Nielsen Damborg", "1854–1940"), ("Jens Nielsen", "(Damborg)", "b. 1856"),
        ("Dorthea Cathrine", "Nielsen", "b. 1860"), ("Ulrica Christine", "Nielsen (Damborg)", "1863–1893")]
for i, (a, b, d) in enumerate(kids):
    line(cc[i], 1520, cc[i], 1570)
    box(COL[i], 1570, BOX, 180, [("b", a), ("b", b), ("s", d)])

label(W / 2, 1850, "Solid lines: parents and marriages · dashed line: foster parents", "middle")

H = 1890
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'font-family="Liberation Serif, Tinos, Times New Roman, serif"><rect width="{W}" height="{H}" fill="#fff"/>'
       + "".join(out) + "</svg>")
open(sys.argv[1], "w", encoding="utf-8").write(svg)
