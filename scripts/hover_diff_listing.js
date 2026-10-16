(async () => {
  const PROPS = ["transform", "filter", "opacity", "backgroundColor", "boxShadow", "clipPath", "color"];
  const snap = (root) => {
    const out = [];
    root.querySelectorAll("*").forEach((el, i) => {
      if (i > 80) return;
      const cs = getComputedStyle(el);
      const rec = {};
      PROPS.forEach(p => { const v = cs[p]; if (v && v !== "none" && v !== "normal" && v !== "0px" && v !== "rgba(0, 0, 0, 0)") rec[p] = v; });
      out.push({ tag: el.tagName, n: el.getAttribute("data-framer-name") || "", rec });
    });
    return out;
  };
  const diff = (a, b) => {
    const d = [];
    for (let k = 0; k < Math.max(a.length, b.length); k++) {
      const A = a[k]?.rec || {}, B = b[k]?.rec || {};
      const dd = {};
      new Set([...Object.keys(A), ...Object.keys(B)]).forEach(p => { if (A[p] !== B[p]) dd[p] = [A[p], B[p]]; });
      if (Object.keys(dd).length) d.push({ k, tag: b[k]?.tag, n: b[k]?.n, dd });
    }
    return d;
  };
  const card = document.querySelector('[data-framer-name="Thumbnail Image"]');
  const scope = card.parentElement;
  card.scrollIntoView({ block: "center" });
  await new Promise(r => setTimeout(r, 2200));   // let entrance animations settle
  const rest1 = snap(scope);
  // simulate hover: dispatch real pointer events (framer-motion listens for pointerenter)
  const ev = (type) => new PointerEvent(type, { bubbles: true, pointerId: 1, isPrimary: true });
  [card, scope].forEach(t => { t.dispatchEvent(ev("pointerover")); t.dispatchEvent(ev("pointerenter")); t.dispatchEvent(ev("pointermove")); });
  await new Promise(r => setTimeout(r, 900));
  const hov = snap(scope);
  // unhover
  [scope, card].forEach(t => { t.dispatchEvent(ev("pointerleave")); t.dispatchEvent(ev("pointerout")); });
  await new Promise(r => setTimeout(r, 900));
  const rest2 = snap(scope);
  return JSON.stringify({
    hover_vs_rest1: diff(rest1, hov),
    rest2_vs_rest1: diff(rest1, rest2),
    hover_vs_rest2: diff(rest2, hov),
  }, null, 1).slice(0, 4000);
})()
