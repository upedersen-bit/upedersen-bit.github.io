# How this website is built

The website at https://upedersen-bit.github.io/ is generated from the biography doc
"Niels Christian Olesen Damborg (1821–1899)" on claude.ai
(https://claude.ai/code/artifact/cac00f94-0aec-4918-95a9-fce8ed603963).
The doc is the master copy. Never edit the published `.html` files by hand; change the doc,
or change the design files here, and rebuild.

Visitors never see this folder: no page links to it.

## Files in `_build/`

| File | What it is |
| --- | --- |
| `build.py` | Turns the doc's markdown export into the site: one page per chapter and appendix, notes folded under "Click here for notes", figures, contents page, sitemap, robots.txt |
| `style.css` | The design: colours, fonts, layout (light and dark) |
| `site.js` | Note pop-ups, folding notes, full-size image viewer |
| `images2.tsv` | One row per picture: doc blob id, alt text as in the doc, asset id. Row 1 = `img/*/fig01.jpg`, row 2 = `fig02.jpg`, and so on |
| `add_image.py` | Resizes a new or replaced picture into `img/web` and `img/full` and records it in `images2.tsv` |

Pictures are matched to the doc by their alt text, so if an alt text changes in the doc, update it in `images2.tsv` too.

## Rebuilding after the doc changes (instructions for Claude)

1. Export the doc tab as markdown: Docs `create` a blob with
   `{"from":{"object":"file","id":"34579559-f347"},"format":"markdown"}` in the doc's container, then
   download it with Artifact `read` (url = the doc, path = the returned asset id).
2. New or changed pictures: read each new blob (`read` object blob) to get its asset id, download it with
   Artifact `read` (one path per call), then run `python3 _build/add_image.py <file> <blob> <asset> "<alt>"`.
3. Build into a temporary folder:
   `python3 _build/build.py <export.md> /tmp/site --updated "<today, e.g. 20 October 2026>"`
4. Copy the result over the repository root: `cp -r /tmp/site/. ./`
   If a page or picture was removed from the doc, also `git rm` its old file (cp does not delete).
5. Look at a few pages on a phone-width and a desktop-width screen, then commit and push to `main`.
   GitHub Pages republishes within a few minutes.

A design change means editing `_build/style.css`, `_build/site.js` or `_build/build.py`, then steps 3–5.

Requirements: Python 3 with the `markdown` and `Pillow` packages.
