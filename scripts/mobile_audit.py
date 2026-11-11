#!/usr/bin/env python3
"""Mobile audit: drive agent-browser at 390px, collect DOM overflow metrics per page."""
import subprocess, json, sys, time

BASE = "http://127.0.0.1:8000"

PUBLIC = [
    ("home", "/"),
    ("properties", "/properties/"),
    ("detail", "/listing/3br-home-near-haller-park-bamburi-8/"),
    ("sale-nyali", "/property-for-sale/nyali/"),
    ("agents", "/agents/"),
    ("login", "/account/login/"),
    ("signup", "/account/signup/"),
]
MANAGE = [
    ("portal", "/manage/"),
    ("enquiries", "/manage/enquiries/"),
    ("enq-detail", "/manage/enquiries/1/"),
    ("listings-tools", "/manage/listings/"),
    ("listing-new", "/manage/listings/new/"),
    ("listing-bulk", "/manage/listings/bulk/"),
    ("brand", "/manage/site-content/"),
    ("categories", "/manage/site-content/categories/"),
    ("media", "/manage/site-content/media/"),
    ("testimonials", "/manage/site-content/testimonials/"),
    ("newsletter", "/manage/site-content/newsletter/"),
    ("seo", "/manage/seo/"),
    ("dashboard", "/dashboard/"),
]

JS = """(() => {
  const de = document.documentElement;
  const vw = de.clientWidth;
  const out = {pageW: de.scrollWidth, innerW: window.innerWidth, overflowX: de.scrollWidth - vw, docH: de.scrollHeight, wideEls: [], wideTables: 0, horizScrollables: []};
  document.querySelectorAll('table').forEach(t => { if (t.scrollWidth > vw + 2 || t.getBoundingClientRect().width > vw + 2) out.wideTables++; });
  document.querySelectorAll('div,section,pre,ul,ol').forEach(el => {
    const cs = getComputedStyle(el);
    if ((cs.overflowX === 'auto' || cs.overflowX === 'scroll') && el.scrollWidth > el.clientWidth + 4) {
      out.horizScrollables.push({cls: (el.className||'').toString().slice(0,40), scrollW: el.scrollWidth, clientW: el.clientWidth});
    }
  });
  if (out.overflowX > 1) {
    const bad = [];
    document.querySelectorAll('body *').forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.right > vw + 2) {
        const cs = getComputedStyle(el);
        if (cs.position === 'fixed') return;
        // only leaf-ish culprits
        if (!el.children.length || cs.overflowX !== 'visible') {
          bad.push({tag: el.tagName.toLowerCase(), cls: (el.className||'').toString().slice(0,50), right: Math.round(r.right), w: Math.round(r.width)});
        }
      }
    });
    out.wideEls = bad.slice(0, 6);
  }
  return JSON.stringify(out);
})()"""

def ab(*args, timeout=60):
    r = subprocess.run(["agent-browser", *args], capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()

def audit(pages, label):
    print(f"########## {label} ##########")
    for name, path in pages:
        url = BASE + path
        try:
            ab("open", url, timeout=45)
            ab("wait", "--load", "networkidle", timeout=30)
        except Exception as e:
            print(f"{name:16s} OPEN-FAIL {e}")
            continue
        time.sleep(0.6)
        try:
            raw = ab("eval", JS, timeout=45)
        except Exception as e:
            print(f"{name:16s} EVAL-FAIL {e}")
            continue
        # agent-browser echoes quoted JSON string
        try:
            s = raw.strip('"').replace('\\"', '"')
            d = json.loads(s)
        except Exception:
            print(f"{name:16s} PARSE-FAIL raw={raw[:120]}")
            continue
        status = "OK " if d["overflowX"] <= 1 else f"OVERFLOW +{d['overflowX']}px"
        print(f"{name:16s} {status:14s} docH={d['docH']:6d} wideTables={d['wideTables']} scrollables={len(d['horizScrollables'])}")
        for e in d["wideEls"][:4]:
            print(f"    culprit: {e['tag']}.{e['cls']} right={e['right']} w={e['w']}")
        for h in d["horizScrollables"][:3]:
            print(f"    scrollable: .{h['cls']} {h['clientW']}->{h['scrollW']}")
        ab("screenshot", f"/tmp/m-audit/{name}.png", timeout=30)

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "public"
    if which == "public":
        audit(PUBLIC, "PUBLIC")
    elif which == "manage":
        audit(MANAGE, "MANAGE")
