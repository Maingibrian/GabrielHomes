(async () => {
  const q = document.querySelector(".site-header__quick");
  if (!q) return "MISSING: .site-header__quick";
  const cs = getComputedStyle(q);
  const btn = q.querySelector(".site-header__quick-btn");
  const b = btn.getBoundingClientRect();
  const burger = document.querySelector(".site-header__hamburger");
  const br = burger.getBoundingClientRect();
  return JSON.stringify({
    visible: cs.display !== "none",
    btnSize: Math.round(b.width) + "x" + Math.round(b.height),
    call: q.querySelectorAll("a")[0].getAttribute("href"),
    wa: q.querySelectorAll("a")[1]?.getAttribute("href"),
    noOverlap: b.right <= br.left,
    vw: innerWidth
  });
})()
