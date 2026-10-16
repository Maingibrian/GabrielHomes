(() => {
  // Global diff harness: snapshot subtree computed styles before/after hover.
  const PROPS = ["transform","filter","opacity","backgroundColor","borderRadius","boxShadow","clipPath","scale","translate","color","letterSpacing"];
  window.__snap = (root) => {
    const out = [];
    root.querySelectorAll("*").forEach((el, i) => {
      if (i > 60) return;
      const cs = getComputedStyle(el);
      const rec = {};
      PROPS.forEach(p => { const v = cs[p]; if (v && v !== "none" && v !== "normal" && v !== "0px" && v !== "rgba(0, 0, 0, 0)") rec[p] = v; });
      out.push({ i, tag: el.tagName, n: el.getAttribute("data-framer-name") || "", s: el.getAttribute("style")?.slice(0, 160) || "", rec });
    });
    return out;
  };
  window.__diff = (a, b) => {
    const diffs = [];
    const n = Math.max(a.length, b.length);
    for (let k = 0; k < n; k++) {
      const A = a[k]?.rec || {}, B = b[k]?.rec || {};
      const keys = new Set([...Object.keys(A), ...Object.keys(B)]);
      const d = {};
      keys.forEach(p => { if (A[p] !== B[p]) d[p] = [A[p], B[p]]; });
      if (Object.keys(d).length) diffs.push({ i: k, tag: b[k]?.tag, n: b[k]?.n, d });
    }
    return diffs;
  };
  const card = document.querySelector('[data-framer-name="Thumbnail Image"]');
  if (!card) return "no card";
  card.scrollIntoView({ block: "center" });
  window.__before = window.__snap(card.parentElement);
  return "armed: " + window.__before.length + " nodes @ " + card.getAttribute("data-framer-name");
})()
