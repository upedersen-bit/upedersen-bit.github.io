#!/usr/bin/env python3
"""Add (or replace) one picture from the biography doc.

Usage: python3 add_image.py <downloaded-image-file> <blob-id> <asset-id> "<alt text exactly as in the doc>"
Writes img/web/figNN.jpg (max 1600 px) and img/full/figNN.jpg (max 3200 px) and records the picture in images2.tsv.
Run it from the folder that holds images2.tsv; the img folder is found next to it or one level up.
"""
import os, sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
src, blob, asset, alt = sys.argv[1:5]
here = os.path.dirname(os.path.abspath(__file__))
tsv = os.path.join(here, "images2.tsv")
img_dir = os.path.join(here, "img") if os.path.isdir(os.path.join(here, "img")) else os.path.join(here, "..", "img")
rows = [l.rstrip("\n").split("\t") for l in open(tsv, encoding="utf-8")]
idx = next((i for i, r in enumerate(rows) if r[0] == blob or r[1] == alt), None)
if idx is None:
    rows.append([blob, alt, asset]); idx = len(rows) - 1
else:
    rows[idx] = [blob, alt, asset]
name = f"fig{idx + 1:02d}"
im = Image.open(src); im.load()
if im.mode in ("RGBA", "LA", "P"):
    im = im.convert("RGBA"); bg = Image.new("RGB", im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[-1]); im = bg
else:
    im = im.convert("RGB")
for d, mx, q in (("web", 1600, 82), ("full", 3200, 86)):
    c = im.copy(); c.thumbnail((mx, mx * 3)); os.makedirs(os.path.join(img_dir, d), exist_ok=True)
    c.save(os.path.join(img_dir, d, name + ".jpg"), quality=q, optimize=True, progressive=True)
open(tsv, "w", encoding="utf-8").write("".join("\t".join(r) + "\n" for r in rows))
print(name, "saved")
