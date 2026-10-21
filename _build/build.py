#!/usr/bin/env python3
"""Build the static website for "Two Names, Two Countries" from the doc's markdown export.

Usage: python3 build.py <doc-export.md> <output-dir> [preview] [--updated "20 October 2026"]
See BUILDING.md in this folder for the full update procedure.
"""
import re, os, sys, shutil, html, json
import markdown

SRC = sys.argv[1]
OUT = sys.argv[2]
PREVIEW = len(sys.argv) > 3 and sys.argv[3] == "preview"
UPDATED = "19 October 2026"
if "--updated" in sys.argv:
    UPDATED = sys.argv[sys.argv.index("--updated") + 1]
BASE_URL = "https://upedersen-bit.github.io/"

md_text = open(SRC, encoding="utf-8").read()
md_text = md_text.replace("&#32;", "")

SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"
SUPMAP = {c: str(i) for i, c in enumerate(SUP)}

# ---- images -------------------------------------------------------------
imgs = [l.rstrip("\n").split("\t") for l in open(os.path.join(os.path.dirname(__file__), "images2.tsv"), encoding="utf-8")]
def norm(s):
    return re.sub(r"[^a-z0-9]", "", html.unescape(s).lower())
img_by_alt = {norm(alt): f"fig{i:02d}" for i, (blob, alt, asset) in enumerate(imgs, 1)}

# ---- fix fragmented bold-italic subheadings & tagline ---------------------
lines = md_text.split("\n")
fixed = []
for ln in lines:
    s = ln.strip()
    if s.startswith("***") and s.endswith("***") and len(s.replace("*", "").strip()) > 0:
        fixed.append("#### " + s.replace("*", "").strip())
    else:
        fixed.append(ln)
md_text = "\n".join(fixed)

# The doc's export splits a caption that was edited in pieces into many italic runs, and writes the
# joins as "**" (e.g. "*The **d**a**te**s*"), which markdown would read as bold. A caption is italic
# from end to end, so inside such a line the "**" joins carry no meaning: remove them.
def fix_caption(ln):
    s = ln.strip()
    if s.startswith("*") and not s.startswith("**") and s.endswith("*") and "**" in s:
        s = s.replace("**", "")
        s = re.sub(r"\* \*", " ", s)          # a plain space between two italic runs
        s = re.sub(r" {2,}", " ", s)
        return s
    return ln
md_text = "\n".join(fix_caption(l) for l in md_text.split("\n"))

# ---- split into sections --------------------------------------------------
# cover = everything before "## Contents"
cover_md, rest = md_text.split("\n## Contents", 1)
rest = rest.split("\n---\n", 1)[1]  # drop the contents list

def split_h2(text):
    parts = re.split(r"^## (.+)$", text, flags=re.M)
    out = []
    for i in range(1, len(parts), 2):
        out.append((parts[i].strip(), parts[i + 1]))
    return out

sections = split_h2(rest)
sec = {t: b for t, b in sections}

# end notes split by ###
notes_body = sec["End Notes"]
notes_intro, notes_rest = notes_body.split("\n### ", 1)
notes_intro = notes_intro.strip()
notes_by = {}
for chunk in ("### " + notes_rest).split("\n### "):
    chunk = chunk.replace("### ", "", 1) if chunk.startswith("### ") else chunk
    title, body = chunk.split("\n", 1)
    items = {}
    cur = None
    for l in body.split("\n"):
        m = re.match(r"^(\d+)\. (.*)$", l)
        if m:
            cur = int(m.group(1)); items[cur] = m.group(2)
        elif cur and l.strip():
            items[cur] += "\n" + l
    notes_by[title.strip()] = items

# ---- page list -------------------------------------------------------------
pages = []  # dict(slug, title, kind, md, notes_key, eyebrow, display, dates)
def add(slug, key, kind, eyebrow, display, dates="", notes_key=None):
    body = sec[key]
    body = re.sub(r"\n---\s*$", "", body.rstrip()) + "\n"
    body = body.replace("\n# Appendices\n", "\n")
    pages.append(dict(slug=slug, key=key, kind=kind, eyebrow=eyebrow, display=display, dates=dates,
                      md=body, notes_key=notes_key))

add("foreword", "Foreword", "front", "Foreword", "Foreword")
add("maps", "Maps of Himmerland and Local Parishes", "front", "Maps", "Himmerland and its parishes")
add("introduction", "Introduction", "front", "Introduction", "Introduction", notes_key="Introduction")
chap_keys = [k for k in sec if re.match(r"^\d\. ", k)]
for k in chap_keys:
    m = re.match(r"^(\d)\. (.+?)(?:, (\d{4}(?:–\d{4})?))?$", k)
    n, t, d = m.group(1), m.group(2), m.group(3) or ""
    add(f"chapter-{n}", k, "chapter", f"Chapter {n}", t, d, notes_key=k)
ep = [k for k in sec if k.startswith("Epilogue")][0]
add("epilogue", ep, "back", "Epilogue", ep.split(": ", 1)[1].capitalize(), notes_key="Epilogue")
for k in [k for k in sec if k.startswith("Appendix ")]:
    m = re.match(r"^Appendix ([A-E]): (.+)$", k)
    add(f"appendix-{m.group(1).lower()}", k, "appendix", f"Appendix {m.group(1)}", m.group(2), notes_key="Appendices")
add("works-cited", "Works Cited", "back", "Sources", "Works Cited")

# ---- conversion helpers ---------------------------------------------------
MD_EXT = ["tables", "sane_lists", "smarty"]
def md2html(s):
    return markdown.markdown(s, extensions=MD_EXT, extension_configs={"smarty": {"smart_quotes": False}})

def md_inline(s):
    h = md2html(s).strip()
    return re.sub(r"^<p>(.*)</p>$", r"\1", h, flags=re.S)

FIGS = []
def figures(body):
    """Turn image placeholders (+ following caption paragraph) into <figure> markers."""
    out = []
    paras = re.split(r"\n\n+", body)
    i = 0
    while i < len(paras):
        p = paras[i].strip()
        m = re.match(r"^&#91;image: (.+?)\\\]$", p)
        if m:
            alt = html.unescape(m.group(1)).replace("\\", "")
            fig = img_by_alt.get(norm(alt))
            if not fig:
                raise SystemExit("no image for " + alt)
            cap = ""
            if i + 1 < len(paras) and paras[i + 1].strip().startswith("*"):
                cap = paras[i + 1].strip(); i += 1
            FIGS.append((fig, alt, cap))
            out.append(f"@@FIG:{len(FIGS)-1}@@")
        else:
            out.append(paras[i])
        i += 1
    return "\n\n".join(out)

def fig_html(fig, alt, cap, sups):
    cap_html = sups(md_inline(cap)) if cap else ""
    # An italic caption: the doc sets captions in italics, with any title inside them in roman.
    # Captions here are already set apart by their own style, so drop the outer italics and
    # flip the inner ones, so that a book or ship title inside a caption is the italic part.
    if cap_html.startswith("<em>") and cap_html.endswith("</em>"):
        inner = cap_html[4:-5]
        inner = inner.replace("</em>", "\x00").replace("<em>", "</em>").replace("\x00", "<em>")
        cap_html = re.sub(r"<em>(\s*)</em>", r"\1", inner)
    return (f'<figure class="fig"><a class="zoom" href="img/full/{fig}.jpg" data-full="img/full/{fig}.jpg">'
            f'<img src="img/web/{fig}.jpg" alt="{html.escape(alt)}" loading="lazy"></a>'
            + (f"<figcaption>{cap_html}</figcaption>" if cap_html else "") + "</figure>")

def make_sups(page_slug, refs):
    """replace runs of superscript digits with note links. refs collects note -> list of ref ids."""
    def rep(m):
        n = int("".join(SUPMAP[c] for c in m.group(0)))
        k = len(refs.setdefault(n, [])) + 1
        rid = f"r{n}-{k}"
        refs[n].append(rid)
        return f'<sup class="nref"><a href="#n{n}" id="{rid}" data-n="{n}">{n}</a></sup>'
    return lambda s: re.sub(f"[{SUP}]+", rep, s)

# captions need sup-links too: do it by running sups on figure captions inside body_html
def body_html_full(page):
    refs = {}
    sups = make_sups(page["slug"], refs)
    body = figures(page["md"])
    h = md2html(body)
    # process in document order so ref ids are sequential
    parts = re.split(r"(<p>@@FIG:\d+@@</p>)", h)
    out = []
    for p in parts:
        mm = re.match(r"<p>@@FIG:(\d+)@@</p>", p)
        if mm:
            fig, alt, cap = FIGS[int(mm.group(1))]
            out.append(fig_html(fig, alt, cap, sups))
        else:
            out.append(sups(p))
    h = "".join(out)
    h = re.sub(r"<blockquote>\s*<p><strong>", '<blockquote class="aside"><p><strong>', h)
    h = h.replace("<blockquote>", '<blockquote class="quote">')
    h = h.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
    h = re.sub(r"<h4>(.*?)</h4>", r'<h2 class="sub">\1</h2>', h)
    h = re.sub(r"<h3>(.*?)</h3>", r'<h2 class="sub">\1</h2>', h)
    h = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', h)
    return h, refs

def notes_html(page, refs):
    key = page["notes_key"]
    if not key:
        return ""
    items = notes_by.get(key, {})
    nums = sorted(items) if page["kind"] != "appendix" else sorted(n for n in items if n in refs)
    if not nums:
        return ""
    lis = []
    for n in nums:
        txt = md_inline(items[n].replace("\n", " "))
        txt = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', txt)
        backs = refs.get(n, [])
        if len(backs) == 1:
            bl = f' <a class="back" href="#{backs[0]}" aria-label="Back to the text">↩</a>'
        elif backs:
            bl = " " + " ".join(f'<a class="back" href="#{r}" aria-label="Back to reference {i}">↩{chr(96+i)}</a>' for i, r in enumerate(backs, 1))
        else:
            bl = ""
        lis.append(f'<li id="n{n}" value="{n}"><span class="nnum">{n}</span><div class="ntext">{txt}{bl}</div></li>')
    intro = md_inline(notes_intro.split(" Short titles")[0]) + ' Short titles refer to the <a href="works-cited.html">Works Cited</a>.'
    count = f'{len(nums)} note' + ("s" if len(nums) != 1 else "")
    return (f'<section class="notes" aria-label="Notes"><details id="notes">'
            f'<summary><span class="sum-open">Click here for notes</span><span class="sum-close">Hide notes</span>'
            f'<span class="sum-count">{count}</span></summary>'
            f'<div class="notes-body"><p class="notes-intro">{intro}</p><ol>{"".join(lis)}</ol></div></details></section>')

# ---- templates ------------------------------------------------------------
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Libre+Caslon+Display&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400;1,8..60,600&family=IBM+Plex+Sans+Condensed:wght@400;500;600&display=swap">')
SITE = "Two Names, Two Countries"

def head(title, desc, main=False):
    meta = (f'<title>{html.escape(title)}</title>'
            '<meta name="claude:viewport-fit-sides" content="cover">'
            f'<meta name="description" content="{html.escape(desc)}">'
            f'<meta property="og:title" content="{html.escape(title)}">'
            f'<meta property="og:description" content="{html.escape(desc)}">'
            '<meta property="og:type" content="book">'
            + FONTS + '<link rel="stylesheet" href="style.css">'
            '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 32 32%22%3E%3Crect width=%2232%22 height=%2232%22 rx=%226%22 fill=%22%232b4d6e%22/%3E%3Ctext x=%2216%22 y=%2223%22 font-family=%22Georgia,serif%22 font-size=%2220%22 text-anchor=%22middle%22 fill=%22%23fff%22%3ED%3C/text%3E%3C/svg%3E">')
    if PREVIEW and main:
        return meta + "\n"
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">' + meta + "</head><body>\n")

def tail(main=False):
    s = '<script src="site.js"></script>'
    if PREVIEW and main:
        return s
    return s + "</body></html>"

def topbar(current=""):
    return (f'<header class="topbar"><div class="topbar-in"><a class="brand" href="index.html">{SITE}</a>'
            f'<a class="toc-link" href="index.html#contents">Contents</a></div></header>')

def footer():
    return (f'<footer class="site-foot"><div class="wrap"><p>Compiled by Leo Pedersen and Ulrik Damborg · Fall 2026 · '
            f'Last revised {UPDATED}</p></div></footer>')

# ---- build -----------------------------------------------------------------
if os.path.exists(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
here = os.path.dirname(os.path.abspath(__file__))
# images: next to this script when building in the work folder, or at the repository root (../img) in the repo
img_src = os.path.join(here, "img") if os.path.isdir(os.path.join(here, "img")) else os.path.join(here, "..", "img")
shutil.copytree(img_src, os.path.join(OUT, "img"))
shutil.copy(os.path.join(here, "style.css"), OUT)
shutil.copy(os.path.join(here, "site.js"), OUT)

def first_sentence(h):
    t = re.sub(r"<[^>]+>", "", h)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\d+(?=\s|$)", "", t) if False else t
    m = re.match(r"(.{40,220}?[.!?])\s", t)
    return (m.group(1) if m else t[:200])

for i, p in enumerate(pages):
    h, refs = body_html_full(p)
    prev_p = pages[i - 1] if i > 0 else None
    next_p = pages[i + 1] if i + 1 < len(pages) else None
    lbl = lambda q: q["display"] if q["eyebrow"] == q["display"] else f'{q["eyebrow"]}: {q["display"]}'
    nav = '<nav class="pager" aria-label="Chapters">'
    nav += (f'<a class="prev" href="{prev_p["slug"]}.html"><span>Previous</span>{lbl(prev_p)}</a>'
            if prev_p else '<a class="prev" href="index.html"><span>Previous</span>Title page and contents</a>')
    nav += (f'<a class="next" href="{next_p["slug"]}.html"><span>Next</span>{lbl(next_p)}</a>'
            if next_p else '<a class="next" href="index.html"><span>Back to</span>Title page and contents</a>')
    nav += "</nav>"
    eyebrow = p["eyebrow"] if p["eyebrow"] != p["display"] else ""
    title_html = (f'<header class="page-head">' + (f'<p class="eyebrow">{eyebrow}</p>' if eyebrow else "")
                  + f'<h1>{p["display"]}</h1>' + (f'<p class="dates">{p["dates"]}</p>' if p["dates"] else "") + "</header>")
    plain = re.sub(r"<sup.*?</sup>", "", h)
    desc = f'{p["eyebrow"]}: {p["display"]}' + (f', {p["dates"]}' if p["dates"] else "") + ". From " + SITE + ", the life of Niels Christian Olesen Damborg, 1821–1899, from Himmerland, Denmark, to Washington County, Nebraska."
    if p["eyebrow"] == p["display"]:
        desc = f'{p["display"]}. From {SITE}, the life of Niels Christian Olesen Damborg, 1821–1899, from Himmerland, Denmark, to Washington County, Nebraska.'
    title = f'{p["eyebrow"]}: {p["display"]} · {SITE}' if eyebrow else f'{p["display"]} · {SITE}'
    page_html = (head(title, desc) + topbar() + f'<main class="wrap {p["kind"]}" id="top">' + title_html
                 + f'<div class="prose">{h}</div>' + notes_html(p, refs) + nav + "</main>" + footer()
                 + '<div class="sheet" id="sheet" hidden role="dialog" aria-label="Note"><div class="sheet-in"><button class="sheet-x" type="button" aria-label="Close note">Close</button><div class="sheet-body"></div></div></div>'
                 + '<div class="lightbox" id="lightbox" hidden role="dialog" aria-label="Image"><button class="lb-x" type="button">Close</button><div class="lb-scroll"><img alt=""></div></div>'
                 + tail())
    open(os.path.join(OUT, p["slug"] + ".html"), "w", encoding="utf-8").write(page_html)

# ---- index (cover + contents) -------------------------------------------------
cv = cover_md
subtitle = re.search(r"^### (.+)$", cv, re.M).group(1)
tagline = re.search(r"^\*(Foster child.+)\*$", cv, re.M).group(1).replace("*", "")
intro_line = re.search(r"^(A family history.+)$", cv, re.M).group(1)
photo_cap = re.search(r"^\*(Photograph of.+?)\*\s*$", cv, re.M).group(1)
compiled = re.search(r"^(Compiled by.+)$", cv, re.M).group(1)

def toc_item(p):
    d = f'<span class="toc-dates">{p["dates"]}</span>' if p["dates"] else ""
    lab = p["eyebrow"].replace("Chapter ", "") if p["kind"] == "chapter" else (p["eyebrow"].replace("Appendix ", "") if p["kind"] == "appendix" else "")
    return f'<li><a href="{p["slug"]}.html"><span class="toc-n">{lab}</span><span class="toc-t">{p["display"]}</span>{d}</a></li>'

front = [p for p in pages if p["kind"] == "front"]
chaps = [p for p in pages if p["kind"] == "chapter"]
apps = [p for p in pages if p["kind"] == "appendix"]
back = [p for p in pages if p["kind"] == "back"]

idx = (head(SITE, f"{subtitle}. {intro_line}", main=True) + topbar()
       + '<main class="wrap cover" id="top">'
       + '<section class="hero">'
       + f'<p class="eyebrow">A family history</p><h1 class="book-title">{SITE}</h1>'
       + f'<p class="book-sub">{subtitle}</p>'
       + '<div class="names" aria-label="His two names">'
       + '<div class="name dk"><span class="label">Denmark, 1821–1866</span><span class="who">Niels Christian Olesen <b>Damborg</b></span></div>'
       + '<div class="name us"><span class="label">Nebraska, 1866–1899</span><span class="who">Nelse C. <b>Olson</b></span></div>'
       + '</div>'
       + f'<p class="tagline">{tagline}</p>'
       + f'<figure class="portrait"><a class="zoom" href="img/full/fig01.jpg" data-full="img/full/fig01.jpg"><img src="img/web/fig01.jpg" alt="Niels Christian Olesen, carte-de-visite by H. Tönnies, Aalborg"></a>'
       + f'<figcaption>{html.escape(photo_cap)}</figcaption></figure>'
       + f'<p class="lede">{html.escape(intro_line)}</p><p class="compiled">{html.escape(compiled)}</p>'
       + f'<p class="start"><a class="btn" href="foreword.html">Start reading</a><a class="btn ghost" href="chapter-1.html">Go to chapter 1</a></p>'
       + '</section>'
       + '<section class="contents" id="contents" aria-labelledby="contents-h"><h2 id="contents-h">Contents</h2>'
       + '<ol class="toc toc-front">' + "".join(toc_item(p) for p in front) + '</ol>'
       + '<h3>Chapters</h3><ol class="toc toc-chap">' + "".join(toc_item(p) for p in chaps) + '</ol>'
       + '<ol class="toc toc-front">' + toc_item(back[0]) + '</ol>'
       + '<h3>Appendices</h3><ol class="toc toc-chap">' + "".join(toc_item(p) for p in apps) + '</ol>'
       + '<ol class="toc toc-front">' + toc_item(back[1]) + '</ol>'
       + '<p class="toc-note">Notes are printed at the end of each chapter. Tap a note number in the text to read the note without leaving your place.</p>'
       + '</section></main>' + footer()
       + '<div class="lightbox" id="lightbox" hidden role="dialog" aria-label="Image"><button class="lb-x" type="button">Close</button><div class="lb-scroll"><img alt=""></div></div>'
       + tail(main=True))
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(idx)

if not PREVIEW:
    open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(
        head("Page not found · " + SITE, "Page not found") + topbar()
        + '<main class="wrap"><header class="page-head"><h1>Page not found</h1></header><div class="prose"><p>That page does not exist. Go to the <a href="index.html">title page and contents</a>.</p></div></main>' + tail())

if not PREVIEW:
    import datetime
    today = datetime.date.today().isoformat()
    locs = [BASE_URL] + [BASE_URL + p["slug"] + ".html" for p in pages]
    open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in locs) + "</urlset>\n")
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}sitemap.xml\n")
    open(os.path.join(OUT, ".nojekyll"), "w").close()

print("pages:", len(pages) + 1)
for p in pages:
    print(p["slug"], "|", p["display"], "|", p["dates"])
