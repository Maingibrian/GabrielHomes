#!/usr/bin/env python3
"""Typography audit r15 — implementation pass (evidence-driven, targeted).

CHANGES (each tied to a measured finding):
  F1. 22 mono blocks use NEGATIVE tracking, contradicting tokens.css's own
      rule "monospace gets POSITIVE tracking — negative crushes it".
      -> letter-spacing: var(--track-tight) -> var(--track-mono) inside
         leaf blocks whose body sets Geist Mono. (search/components/pages/
         detail/dashboard CSS)
  F2. Sub-13px text behind login (violates the site's own 13px UI floor):
      .status-badge + .image-formset__label 10px -> var(--text-xs).
  F3. admin-studio.css 12-12.8px stragglers -> 0.8125rem (13px floor);
      hardcoded family names -> tokens (consistency).
  F4. Measure overshoot: ch units in Geist render ~20% wider than the
      character counts they suggest. Measured 84-98 chars/line on
      .story__body p (target 45-75) and .prose > * at 72ch (~100 chars).
      -> story 58ch -> 47ch; prose 72ch -> 50ch; detail description capped.
  F5. Centralize long-form leading: --leading-prose: 1.65 token, applied
      to .story__body p (was hardcoded 1.65).
  F6. base.html: preload Geist + Fraunces woff2 (hero paints in the right
      face on first paint; measured 290KB total, swap already set).
NOT changed (justified): font families (current system wins), 16px/1.3
body for UI density, heading scale, weights, Fraunces optical sizing.
"""
import re
import pathlib

CSS = pathlib.Path("/home/z/my-project/gabriel_homes/static/css")
MONO_RE = re.compile(r'font-family:[^;]*(--font-mono|"Geist Mono")')
log = []


def leaf_blocks(text):
    """Yield (start, end) spans of leaf {} blocks (no nested braces)."""
    out, depth, start = [], 0, None
    for i, ch in enumerate(text):
        if ch == "{":
            depth += 1
            if depth == 1:
                start = i + 1
        elif ch == "}":
            if depth == 1 and start is not None:
                out.append((start, i))
                start = None
            depth -= 1
    return out


def fix_mono_tracking(path):
    text = path.read_text()
    n = 0
    for s, e in reversed(leaf_blocks(text)):
        body = text[s:e]
        if MONO_RE.search(body) and "letter-spacing: var(--track-tight)" in body:
            new = body.replace("letter-spacing: var(--track-tight)",
                               "letter-spacing: var(--track-mono)")
            text = text[:s] + new + text[e:]
            n += 1
    log.append(f"F1 {path.name}: {n} mono blocks -> track-mono")
    path.write_text(text)


def fix_dashboard(path):
    text = path.read_text()
    n = text.count("font-size: 10px")
    text = text.replace("font-size: 10px", "font-size: var(--text-xs)")
    log.append(f"F2 {path.name}: {n} x 10px -> var(--text-xs)")
    path.write_text(text)


def fix_admin(path):
    text = path.read_text()
    c1 = text.count("font-size: 0.8rem")
    text = text.replace("font-size: 0.8rem", "font-size: 0.8125rem")
    c2 = text.count("font-size: 0.75rem")
    text = text.replace("font-size: 0.75rem", "font-size: 0.8125rem")
    c3 = len(re.findall(r'font-family:\s*"Geist Mono",\s*monospace', text))
    text = re.sub(r'font-family:\s*"Geist Mono",\s*monospace',
                  "font-family: var(--font-mono)", text)
    c4 = len(re.findall(r'font-family:\s*"Geist",\s*sans-serif', text))
    text = re.sub(r'font-family:\s*"Geist",\s*sans-serif',
                  "font-family: var(--font-sans)", text)
    log.append(f"F3 {path.name}: 0.8rem x{c1} + 0.75rem x{c2} -> 0.8125rem; "
               f"families tokenized x{c3 + c4}")
    path.write_text(text)


def fix_measures(home, pages, detail, tokens):
    t = tokens.read_text()
    assert "--leading-body:" in t
    if "--leading-prose" not in t:
        t = t.replace("  --leading-body:  1.3;",
                      "  --leading-body:  1.3;\n  --leading-prose: 1.65; /* long-form reading (r15 audit) */")
    tokens.write_text(t)
    log.append("F5 tokens.css: + --leading-prose: 1.65")

    h = home.read_text()
    old = """.story__body p {
  font-size: var(--text-base);
  line-height: 1.65;
  color: color-mix(in srgb, var(--ink) 78%, var(--taupe));
  max-width: 58ch;
}"""
    new = """.story__body p {
  font-size: var(--text-base);
  line-height: var(--leading-prose);
  color: color-mix(in srgb, var(--ink) 78%, var(--taupe));
  max-width: 47ch; /* r15: 58ch measured 84-98 real chars; 47ch ~68 */
}"""
    assert old in h, "story block drifted"
    h = h.replace(old, new)
    home.write_text(h)
    log.append("F4 home.css: story 58ch->47ch, leading -> var(--leading-prose)")

    p = pages.read_text()
    assert ".prose > * {\n  max-width: 72ch;\n}" in p
    p = p.replace(".prose > * {\n  max-width: 72ch;\n}",
                  ".prose > * {\n  max-width: 50ch; /* r15: 72ch ~100 real chars in Geist */\n}")
    pages.write_text(p)
    log.append("F4 pages.css: prose 72ch->50ch")

    d = detail.read_text()
    old_d = """.detail-description__body {
  font-size: var(--text-md);
  line-height: var(--leading-body);"""
    new_d = """.detail-description__body {
  font-size: var(--text-md);
  max-width: 52ch; /* r15: cap measure at ~70 real chars */
  line-height: var(--leading-body);"""
    assert old_d in d
    d = d.replace(old_d, new_d)
    detail.write_text(d)
    log.append("F4 detail.css: description capped at 52ch")


def fix_preload(base_html):
    t = base_html.read_text()
    if "rel=\"preload\"" in t and "Geist-Variable" in t:
        log.append("F6 base.html: preload already present")
        return
    preloads = (
        '  <link rel="preload" href="{% staticv \'fonts/Geist-Variable.woff2\' %}" '
        'as="font" type="font/woff2" crossorigin>\n'
        '  <link rel="preload" href="{% staticv \'fonts/Fraunces-Variable-normal.woff2\' %}" '
        'as="font" type="font/woff2" crossorigin>\n'
    )
    marker = "{% block scripts %}"
    assert marker in t
    t = t.replace(marker, preloads + marker, 1)
    base_html.write_text(t)
    log.append("F6 base.html: preload Geist + Fraunces normal")


if __name__ == "__main__":
    fix_mono_tracking(CSS / "search.css")
    fix_mono_tracking(CSS / "components.css")
    fix_mono_tracking(CSS / "pages.css")
    fix_mono_tracking(CSS / "detail.css")
    fix_mono_tracking(CSS / "dashboard.css")
    fix_mono_tracking(CSS / "home.css")
    fix_dashboard(CSS / "dashboard.css")
    fix_admin(CSS / "admin-studio.css")
    fix_measures(CSS / "home.css", CSS / "pages.css", CSS / "detail.css", CSS / "tokens.css")
    fix_preload(pathlib.Path("/home/z/my-project/gabriel_homes/templates/base.html"))
    print("\n".join(log))
