"""r18 H1 — CSS moves for the section re-homing.

1. home.css: the .newsletter-form block moves OUT (footer is site-wide now;
   home.css only loads on pages that opt in). The unused --light variant
   goes away with it (nothing renders it after the band moved).
2. components.css: gains the (dark) newsletter form + the new footer rows
   (cta, browse column, faq) — tokens/color-mix only, zero new hex.
3. pages.css: .commit-list for the checks-page commitments.
4. home.css: spacing for the in-market talk strip.
"""
from pathlib import Path

CSS = Path("/home/z/my-project/gabriel-homes/static/css")

# --- 1+4. home.css ----------------------------------------------------------
home = (CSS / "home.css").read_text(encoding="utf-8")
start = home.index("/* ---- newsletter sign-up (index)")
end = home.index("/* ---- curated Mombasa listing sections")
block = home[start:end]
assert ".newsletter-form--light" in block
home = home[:start] + home[end:]

# talk strip sits inside the recommended section, after the stay group
home = home.replace(
    "/* ---- curated Mombasa listing sections ------------------------ */",
    "/* H1 r18: talk-to-us strip lives inside the recommended section */\n"
    ".home-market__talk { margin-top: clamp(3rem, 5vw, 4.5rem); padding-top: 2.5rem;"
    " border-top: 1px solid var(--sand-60, rgba(216,201,184,.6)); }\n\n"
    "/* ---- curated Mombasa listing sections ------------------------ */",
    1,
)
(CSS / "home.css").write_text(home, encoding="utf-8")

# keep only the dark variant (drop --light rules line-by-line)
dark = [ln for ln in block.splitlines() if "--light" not in ln]
newsletter_css = "\n".join(dark).replace(
    "/* ---- newsletter sign-up (index) ------------------------------- */",
    "/* ---- newsletter sign-up (site-wide footer since H1/r18) ------ */",
)

# --- 2. components.css -------------------------------------------------------
comp = (CSS / "components.css").read_text(encoding="utf-8")

old_grid = "@media (min-width: 810px) {\n  .footer-cols { grid-template-columns: repeat(4, 1fr); gap: 3rem; }\n}"
new_grid = (
    "@media (min-width: 810px) {\n"
    "  .footer-cols { grid-template-columns: repeat(4, 1fr); gap: 3rem; }\n"
    "}\n"
    "@media (min-width: 1200px) {\n"
    "  .footer-cols { grid-template-columns: repeat(5, 1fr); gap: 2.5rem; }\n"
    "}"
)
assert old_grid in comp
comp = comp.replace(old_grid, new_grid, 1)

footer_css = """

/* ============================================================
   12b. Footer rows added by H1 (r18) — CTA, browse, newsletter, FAQ
   ============================================================ */
.site-footer__cta {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem 3rem;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 2.5rem;
  border-bottom: 1px solid color-mix(in srgb, var(--sand) 18%, transparent);
}
.site-footer__cta-title {
  font-size: var(--text-3xl);
  font-weight: 500;
  color: var(--cream);
  letter-spacing: var(--track-tighter);
  line-height: var(--leading-tight);
  margin: 0.5rem 0 0.75rem;
}
.site-footer__cta-sub {
  color: color-mix(in srgb, var(--cream) 75%, transparent);
  max-width: 52ch;
  margin: 0;
}
.site-footer__row {
  border-top: 1px solid color-mix(in srgb, var(--sand) 18%, transparent);
  padding-top: 2.5rem;
}
.site-footer__newsletter {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.75rem;
}
@media (min-width: 1000px) {
  .site-footer__newsletter { grid-template-columns: 1.1fr 1fr; gap: 4rem; align-items: start; }
}
.site-footer__newsletter-note {
  color: color-mix(in srgb, var(--cream) 75%, transparent);
  max-width: 48ch;
  margin-top: 0.75rem;
}
.footer-cols__subhead {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: color-mix(in srgb, var(--cream) 55%, transparent);
  margin: 0.9rem 0 0.15rem;
}
.footer-cols__subhead:first-of-type { margin-top: 0; }
.footer-cols__count {
  color: color-mix(in srgb, var(--cream) 45%, transparent);
  font-size: var(--text-xs);
  margin-left: 0.35rem;
}
.footer-faq__title {
  font-size: var(--text-xl);
  font-weight: 500;
  color: var(--cream);
  letter-spacing: var(--track-tighter);
  margin-bottom: 1.25rem;
}
.footer-faq__list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
  max-width: 60rem;
}
@media (min-width: 810px) {
  .footer-faq__list { grid-template-columns: 1fr 1fr; gap: 0 3rem; }
}
.footer-faq__list details {
  border-bottom: 1px solid color-mix(in srgb, var(--sand) 14%, transparent);
}
.footer-faq__list summary {
  cursor: pointer;
  padding: 0.85rem 0;
  color: var(--cream);
  font-size: var(--text-sm);
  font-weight: 500;
  list-style-position: outside;
}
.footer-faq__list summary::marker { color: var(--burnt); }
.footer-faq__list details p {
  color: color-mix(in srgb, var(--cream) 70%, transparent);
  font-size: var(--text-sm);
  padding: 0 0 0.9rem;
  max-width: 52ch;
}

/* ---- newsletter sign-up (site-wide footer since H1/r18) ------ */
""" + newsletter_css.strip() + "\n"
comp = comp.rstrip() + footer_css
(CSS / "components.css").write_text(comp, encoding="utf-8")

# --- 3. pages.css ------------------------------------------------------------
pages = (CSS / "pages.css").read_text(encoding="utf-8")
pages = pages.rstrip() + """

/* H1 r18: commitments list on /checks/ (moved from the home band) */
.commit-list {
  list-style: none;
  margin: 2rem 0 0;
  padding: 0;
  display: grid;
  gap: 1.25rem;
  max-width: 62rem;
}
.commit-list li {
  background: var(--white, #fff);
  border: 1px solid var(--sand);
  border-radius: var(--radius-md, 14px);
  padding: 1.25rem 1.5rem;
  color: var(--brown);
  line-height: 1.55;
}
.commit-list strong { display: block; color: var(--ink); margin-bottom: 0.3rem; }
"""
(CSS / "pages.css").write_text(pages, encoding="utf-8")

# --- verify: no newsletter-form left in home.css, present in components -----
home2 = (CSS / "home.css").read_text(encoding="utf-8")
comp2 = (CSS / "components.css").read_text(encoding="utf-8")
assert "newsletter-form" not in home2
assert ".newsletter-form {" in comp2
assert "--light" not in comp2.split("newsletter sign-up")[1]
import re
new_hex = len(re.findall(r"#[0-9a-fA-F]{3,8}", footer_css))
print(f"CSS OK — new rules added, {new_hex} hex literals in additions "
      f"(fallbacks only, ratchet-safe)")
