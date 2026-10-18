#!/usr/bin/env python3
"""r12 contrast math — pick token values that pass WCAG AA.

Luminance/contrast per WCAG 2.x. Alpha pairs are composited over the
stated backdrop first, then the ratio is computed on the solid result.
"""
import sys

def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def lum(rgb):
    r, g, b = rgb
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)

def ratio(fg, bg):
    l1, l2 = sorted((lum(fg), lum(bg)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)

def hx(s):
    s = s.lstrip('#')
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))

def mix(fg, a, bg):
    return tuple(round(a * f + (1 - a) * b) for f, b in zip(fg, bg))

def show(label, fg, bg, need):
    r = ratio(fg, bg)
    flag = 'PASS' if r >= need else 'FAIL'
    print(f"{flag}  {r:5.2f}:1 (need {need})  {label}  "
          f"fg=#{fg[0]:02x}{fg[1]:02x}{fg[2]:02x} bg=#{bg[0]:02x}{bg[1]:02x}{bg[2]:02x}")
    return r

# ---- palette ----
CREAM  = hx('faf8f4'); WHITE = hx('ffffff'); SAND  = hx('d8c9b8')
TAUPE  = hx('8a7d70'); CLAY  = hx('a66a4d'); BROWN = hx('5a4032')
ESP    = hx('2a211c'); INK   = hx('211e1b'); BURNT = hx('af4715')
WA_GREEN = hx('25d366'); ADMIN_TH = hx('f0e9df')

mode = sys.argv[1] if len(sys.argv) > 1 else 'explore'

if mode == 'explore':
    print('== 1. muted-ink (taupe) candidates — need 4.5 on white/cream/admin-th ==')
    for c in ('6f6257', '6b5e53', '675a50', '63564c'):
        t = hx(c)
        show(f'taupe {c} on white', t, WHITE, 4.5)
        show(f'taupe {c} on cream', t, CREAM, 4.5)
        show(f'taupe {c} on adminth', t, ADMIN_TH, 4.5)

    print('\n== 2. clay candidates — need 4.5 on cream ==')
    for c in ('965634', '8f5232', '9a5a38', '8a4d2f'):
        show(f'clay {c} on cream', hx(c), CREAM, 4.5)

    print('\n== 3. header accent candidates — need 4.5 on espresso ==')
    for c in ('eda07a', 'f0a87e', 'e89a70', 'f2b18a'):
        show(f'accent {c} on espresso', hx(c), ESP, 4.5)

    print('\n== 4. whatsapp text candidates — need 4.5 on #25d366 ==')
    for c in ('0b3b2e', '093826', '073324', '0d4536'):
        show(f'wa-text {c} on green', hx(c), WA_GREEN, 4.5)

    print('\n== 5. published-badge text — bg = 18% green over white ==')
    bg18 = mix(WA_GREEN, 0.18, WHITE)
    for c in ('128c7e', '0b6b52', '0a5f49', '09543f'):
        show(f'badge {c}', hx(c), bg18, 4.5)

    print('\n== 6. pagination disabled (ink @ opacity over white) ==')
    for a in (0.4, 0.55, 0.6, 0.65):
        show(f'ink @{a}', mix(INK, a, WHITE), WHITE, 3.0)

    print('\n== 7. bento scrim: cream text over scrim(strength a) over white photo ==')
    for a in (0.6, 0.75, 0.88, 0.95, 0.97):
        bg = mix(ESP, a, WHITE)  # worst-case: pure white photo behind
        show(f'cream on scrim a={a}', CREAM, bg, 4.5)
        show(f'  sand  on scrim a={a}', SAND, bg, 4.5)

    print('\n== 8. story quote: burnt @ rest-opacity on cream (28px -> need 3) ==')
    for a in (0.14, 0.45, 0.5, 0.55, 0.6):
        show(f'burnt @{a}', mix(BURNT, a, CREAM), CREAM, 3.0)

    print('\n== 9. monogram espresso on sand; verified brown on cream ==')
    show('espresso on sand', ESP, SAND, 4.5)
    show('brown on cream', BROWN, CREAM, 4.5)

    print('\n== 10. delivery page (workspace_server) ==')
    DPBG = hx('faf7f2')
    for c in ('a8400f', 'a03d18', '9c3a16'):
        show(f'kicker {c} on #faf7f2', hx(c), DPBG, 4.5)
    for c in ('7a6f63', '6b6055', '655a4e'):
        show(f'lead {c} on #faf7f2', hx(c), DPBG, 4.5)
    for c in ('c25e3a', 'b04a1a', 'a8430f'):
        show(f'white on btn {c}', WHITE, hx(c), 4.5)

    print('\n== 11. current pairs (documented failures) ==')
    show('burnt on espresso (nav index/brand)', BURNT, ESP, 4.5)
    show('white on wa-green', WHITE, WA_GREEN, 4.5)
    show('taupe on cream', TAUPE, CREAM, 4.5)
    show('clay on cream', CLAY, CREAM, 4.5)

if mode == 'verify':
    ok = True
    def chk(label, fg, bg, need):
        global ok
        r = ratio(fg, bg)
        good = r >= need
        ok = ok and good
        print(f"{'PASS' if good else 'FAIL'}  {r:5.2f}:1 (need {need})  {label}")

    print('-- item 1: muted-ink token --')
    chk('taupe 6b5e53 on white', hx('6b5e53'), WHITE, 4.5)
    chk('taupe 6b5e53 on cream', hx('6b5e53'), CREAM, 4.5)
    chk('taupe 6b5e53 on admin-th', hx('6b5e53'), ADMIN_TH, 4.5)
    print('-- item 1b: clay token --')
    chk('clay 965634 on cream', hx('965634'), CREAM, 4.5)
    print('-- item 2: header brand + nav index on espresso --')
    chk('ember eda07a on espresso', hx('eda07a'), ESP, 4.5)
    print('-- item 3: whatsapp pair --')
    chk('0b3b2e on wa-green', hx('0b3b2e'), WA_GREEN, 4.5)
    print('-- item 4: story quote states + hero accent --')
    chk('quote rest ink50 on cream', mix(INK, 0.5, CREAM), CREAM, 3.0)
    chk('quote lit burnt on cream', BURNT, CREAM, 4.5)
    hero_bg = mix(ESP, 0.657, WHITE)  # worst-case white photo through scrim
    chk('hero accent clay30 on scrim', mix(hx('965634'), 0.30, CREAM), hero_bg, 3.0)
    chk('hero cream title on scrim', CREAM, hero_bg, 4.5)
    print('-- item 5: bento scrim / badges / founder / pagination --')
    for a, zone in ((0.74, 'upper text'), (0.96, 'bottom text')):
        chk(f'cream on scrim {zone} (a={a})', CREAM, mix(ESP, a, WHITE), 4.5)
        chk(f'sand  on scrim {zone} (a={a})', SAND, mix(ESP, a, WHITE), 4.5)
    chk('published green-deep on tint', hx('0b6b52'), mix(WA_GREEN, 0.18, WHITE), 4.5)
    chk('demo/under-offer brown on burnt tint', BROWN, mix(BURNT, 0.18, CREAM), 4.5)
    chk('pagination ink@0.55', mix(INK, 0.55, WHITE), WHITE, 3.0)
    chk('founder cream on espresso-88', CREAM, mix(ESP, 0.88, WHITE), 4.5)
    print('-- item 5b: monogram / verified --')
    chk('monogram espresso on sand', ESP, SAND, 4.5)
    chk('verified brown on cream', BROWN, CREAM, 4.5)
    print('-- delivery page (:3000) --')
    DP = hx('faf7f2')
    chk('kicker a03d18', hx('a03d18'), DP, 4.5)
    chk('lead 655a4e', hx('655a4e'), DP, 4.5)
    chk('white on btn b04a1a', WHITE, hx('b04a1a'), 4.5)
    print('ALL PASS' if ok else 'SOME FAILED')
    sys.exit(0 if ok else 1)
