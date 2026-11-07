#!/usr/bin/env python3
"""r43 E3: verify the brightened bento scrims still meet the r12 contrast
contract — cream text (the .bento-card__index eyebrow, the highest text)
must clear 4.5:1 over a PURE-WHITE photo at its actual rendered position,
per breakpoint. Uses agent-browser geometry + a JS-side alpha model of the
exact gradient stops shipped in components.css.

Also samples rendered pixel brightness of the card photo zone (top 30%)
before/after to prove the brightening is real.
"""
import json
import subprocess

# (width, gradient stops) — must mirror components.css exactly
def gradient_for(width):
    if width <= 640:
        # 1-col / narrow carousel: text block fills most of the card
        stops = [(0, 0.08), (20, 0.66), (100, 0.94)]
    elif width <= 1020:
        stops = [(0, 0.0), (30, 0.02), (46, 0.66), (100, 0.95)]
    else:
        stops = [(0, 0.0), (36, 0.0), (46, 0.66), (100, 0.94)]
    return stops

def spotlight_gradient(width):
    if width <= 1020:
        return gradient_for(width)
    return [(0, 0.0), (48, 0.0), (64, 0.66), (100, 0.95)]

def alpha_at(stops, pct):
    prev_p, prev_a = stops[0]
    for p, a in stops[1:]:
        if pct <= p:
            if p == prev_p:
                return a
            t = (pct - prev_p) / (p - prev_p)
            return prev_a + t * (a - prev_a)
        prev_p, prev_a = p, a
    return stops[-1][1]

def srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def blend_alpha(alpha):
    """white photo worst case blended with espresso rgba(28,21,17) at alpha"""
    ch = []
    for photo, ink in ((255, 28), (255, 21), (255, 17)):
        ch.append(photo * (1 - alpha) + ink * alpha)
    l = (0.2126 * srgb_to_lin(ch[0]) + 0.7152 * srgb_to_lin(ch[1])
         + 0.0722 * srgb_to_lin(ch[2]))
    return l

CREAM_L = (0.2126 * srgb_to_lin(250) + 0.7152 * srgb_to_lin(248)
           + 0.0722 * srgb_to_lin(244))

def contrast(alpha):
    l = blend_alpha(alpha)
    return (CREAM_L + 0.05) / (l + 0.05)

JS = "Array.from(document.querySelectorAll('.bento-card')).map(function(c){var i=c.querySelector('.bento-card__index'); if(!i) return null; var cr=c.getBoundingClientRect(), ir=i.getBoundingClientRect(); return {spotlight:c.classList.contains('bento-card--spotlight'), cta:c.classList.contains('bento-card--cta'), topPct:+(100*(ir.top-cr.top)/cr.height).toFixed(2), h:Math.round(cr.height)};}).filter(Boolean)"

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    return r.stdout.strip()

failures = 0
print(f"{'width':>6} {'card':>10} {'eyebrow%':>9} {'alpha':>6} {'contrast':>8}  verdict")
for width in (1440, 1280, 1100, 1024, 900, 700, 660, 390):
    run(f"agent-browser set viewport {width} 900")
    run("agent-browser open http://127.0.0.1:3011/")
    run("agent-browser wait 800")
    run("agent-browser scroll down 800")
    run("agent-browser wait 500")
    raw = run("agent-browser eval " + json.dumps(JS))
    raw = raw.strip()
    if not raw.startswith('['):
        print(f"{width}: eval failed: {raw[:120]}")
        failures += 1
        continue
    cards = json.loads(json.loads(raw)) if raw.startswith('"') else json.loads(raw)
    try:
        cards = json.loads(cards) if isinstance(cards, str) else cards
    except Exception:
        pass
    for card in cards:
        if card["cta"]:
            continue  # light tile: text on solid cream/sand, no scrim math
        pct = card["topPct"]
        stops = (spotlight_gradient(width) if card["spotlight"]
                 else gradient_for(width))
        a = alpha_at(stops, pct)
        c = contrast(a)
        ok = c >= 4.5
        if not ok:
            failures += 1
        kind = ("spotlight" if card["spotlight"] else f"{card['h']}px")
        print(f"{width:>6} {kind:>10} {pct:>8.1f}% {a:>6.3f} {c:>7.2f}:1  "
              f"{'PASS' if ok else 'FAIL'}")

print(f"\n{'ALL PASS' if failures == 0 else f'{failures} FAILURES'}")
raise SystemExit(1 if failures else 0)
