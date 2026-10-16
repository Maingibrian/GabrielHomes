(() => {
  const img = [...document.querySelectorAll('[data-framer-name="image"]')].find(e => e.getBoundingClientRect().width > 200);
  if (!img) return "none";
  const cs = getComputedStyle(img);
  return JSON.stringify({ n: img.getAttribute("data-framer-name"), transform: cs.transform });
})()
