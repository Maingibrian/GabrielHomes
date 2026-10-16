(() => {
  const PROPS = ["transform","filter","opacity","backgroundColor","boxShadow","clipPath","color"];
  const card = document.querySelector('[data-framer-name="Thumbnail Image"]');
  const scope = card.parentElement;
  const out = [];
  scope.querySelectorAll("*").forEach((el, i) => {
    if (i > 80) return;
    const cs = getComputedStyle(el);
    const rec = {};
    PROPS.forEach(p => { const v = cs[p]; if (v && v !== "none" && v !== "normal" && v !== "0px" && v !== "rgba(0, 0, 0, 0)") rec[p] = v; });
    out.push({ tag: el.tagName, n: el.getAttribute("data-framer-name") || "", rec });
  });
  return JSON.stringify(out);
})()
