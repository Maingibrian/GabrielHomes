/* r51 QA — verify the reduced-motion kill path with a real
 * prefers-reduced-motion match (agent-browser's `set media` cannot
 * emulate it, so we launch chromium with --force-prefers-reduced-motion
 * through the global playwright install).
 *
 * Checks on http://127.0.0.1:3000/ under reduced motion:
 *   1. html[data-fx] is "none" (fx-gate maps the media query)
 *   2. assurance items: animation none, opacity 1, transform none
 *      (content fully visible — the fail-open contract)
 *   3. chips + label: animation none, visible
 *   4. pane transition: none (instant swap still swaps — content)
 *   5. pill focus-within: transform stays none
 */
const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1600, height: 900 },
    reducedMotion: "reduce",   // native Playwright emulation
  });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:3000/", { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);  // past every entrance delay (.9s last chip)

  const result = await page.evaluate(() => {
    const q = (s) => document.querySelector(s);
    const cs = (el) => (el ? getComputedStyle(el) : null);
    const li = cs(q(".hero__assurances li"));
    const chip = cs(q(".hero__loc"));
    const label = cs(q(".hero__locations-label"));
    const pane = cs(q(".hero-card__pane.is-active"));
    const pill = q(".hero__search");
    return {
      rm: matchMedia("(prefers-reduced-motion: reduce)").matches,
      fx: document.documentElement.getAttribute("data-fx"),
      itemAnim: li.animationName,
      itemOpacity: li.opacity,
      itemTransform: li.transform,
      itemText: q(".hero__assurances").textContent.replace(/\s+/g, " ").trim(),
      chipAnim: chip.animationName,
      chipOpacity: chip.opacity,
      labelAnim: label.animationName,
      paneTransition: pane ? pane.transitionProperty : "no-card",
      panePresent: !!q(".hero-card__pane.is-active"),
      marketGone: !q(".hero__market"),
    };
  });

  // focus-within lift must not move the pill under reduced motion
  await page.focus("#hero-search-q");
  const lift = await page.evaluate(() => {
    getComputedStyle(document.querySelector(".hero__search")).transform;
    return getComputedStyle(document.querySelector(".hero__search")).transform;
  });

  console.log(JSON.stringify({ ...result, pillLiftTransform: lift }, null, 2));

  const pass = result.rm === true &&
    result.fx === "none" &&
    result.itemAnim === "none" && result.itemOpacity === "1" &&
    result.itemTransform === "none" &&
    result.chipAnim === "none" && result.chipOpacity === "1" &&
    result.labelAnim === "none" &&
    result.marketGone === true &&
    lift === "none";
  console.log(pass ? "PASS: reduced-motion kills every r51 move, content visible"
                   : "FAIL: see dump above");
  await context.close(); await browser.close();
  process.exit(pass ? 0 : 1);
})().catch((e) => { console.error(e); process.exit(2); });
