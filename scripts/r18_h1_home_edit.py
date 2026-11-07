"""r18 H1 — surgical home.html restructure (marker-based, verified).

Changes:
  1. hero section id: top -> hero   (runbook H1: id order hero,bento,...)
  2. showcase section id: showcase -> bento
  3. talk-to-us channels strip moves INSIDE the recommended section
     (runbook §6 H1: recommended carries WhatsApp/phone/email)
  4. removes the standalone sections: talk-to-us band, about, services,
     commitments, browse, faq, newsletter, cta  (content is re-homed in
     checks.html / about.html / _footer.html by the caller edits)

Verifies the result: exactly [hero, bento, recommended, nearby].
"""
import re
from pathlib import Path

P = Path("/home/z/my-project/gabriel-homes/templates/core/home.html")
src = P.read_text(encoding="utf-8")

# --- 1+2. ids ---------------------------------------------------------------
assert 'id="top"' in src and 'id="showcase"' in src
src = src.replace('<section class="hero" id="top">',
                  '<section class="hero" id="hero">', 1)
src = src.replace('<section class="section showcase" id="showcase">',
                  '<section class="section showcase" id="bento">', 1)

# --- 4a. delete the talk-to-us band (comment + {% if %} ... {% endif %}) ----
m = re.search(
    r"\{# Talk-to-us band.*?\{% endif \%\}\n", src, re.S)
assert m, "talk-to-us band not found"
src = src[:m.start()] + src[m.end():]

# --- 3. insert the channels strip inside the recommended section -----------
STRIP = """    {% endif %}

    <div class="home-market__talk" data-reveal>
      <p class="section-tag section-tag--rule">[ TALK TO US ]</p>
      <h2 class="home-social__title">One message, three ways to send it.</h2>
      <p class="home-social__sub">Ask about any home above — a person replies, whatever the channel.</p>
      <div class="home-social__links">
        {% if brand.whatsapp %}
        <a class="home-social__link" href="https://wa.me/{{ brand.whatsapp_digits }}" rel="noopener">
          <strong>WhatsApp</strong><span>Message us any time</span>
        </a>
        {% endif %}
        {% if brand.phone %}
        <a class="home-social__link" href="tel:{{ brand.phone }}">
          <strong>Call</strong><span>{{ brand.phone }}</span>
        </a>
        {% endif %}
        {% if brand.email %}
        <a class="home-social__link" href="mailto:{{ brand.email }}">
          <strong>Email</strong><span>{{ brand.email }}</span>
        </a>
        {% endif %}
      </div>
    </div>
"""
anchor = '    {% endif %}\n  </div>\n</section>\n{% endif %}'
assert src.count(anchor) == 1, f"market tail anchor count = {src.count(anchor)}"
src = src.replace(anchor, STRIP + anchor, 1)

# --- 4b. delete everything from the ABOUT comment to the CTA close ---------
m = re.search(
    r"\{# =+\ #\}\n\{# 4\. ABOUT.*?</section>\n+(?=\{% endblock)",
    src, re.S)
assert m, "about..cta tail not found"
src = src[:m.start()] + src[m.end():]

P.write_text(src, encoding="utf-8")

# --- verification -----------------------------------------------------------
ids = re.findall(r'<section[^>]*\bid="([^"]+)"', src)
assert ids == ["hero", "bento", "recommended", "nearby"], ids
for gone in ('id="talk-to-us"', 'id="about"', 'id="services"',
             'id="commitments"', 'id="browse"', 'id="faq"',
             'id="newsletter"', 'id="cta"'):
    assert gone not in src, f"{gone} still present"
assert "home-social__links" in src  # strip kept (inside recommended)
n_sections = len(re.findall(r"<section\b", src))
print(f"home.html OK — sections: {ids} (count {n_sections}, "
      f"{len(src.splitlines())} lines)")
