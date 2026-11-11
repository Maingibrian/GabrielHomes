"""r73 — the portal must load the real design system.

THE LATENT BUG (found live in r73): manage/base.html linked only
base.css + manage.css. Since r42 moved tokens/components out of
base.css's @import chain, EVERY var(--token) in the portal computed
invalid — transparent topbar, fallback colors, invisible chart bars.
The portal "worked" because layout properties don't read tokens; it
just never wore its own design. Pinned here so the stylesheet set and
order can never silently shrink again.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BASE = REPO / "templates" / "manage" / "base.html"


def _links() -> list[str]:
    src = BASE.read_text()
    out = []
    for line in src.splitlines():
        line = line.strip()
        if line.startswith('<link rel="stylesheet"'):
            start = line.index("'css/") + 1
            end = line.index("'", start)
            out.append(line[start:end].removeprefix("css/"))
    return out


def test_portal_links_the_full_design_stack():
    links = _links()
    assert links == ["tokens.css", "base.css", "components.css", "manage.css"], (
        f"Portal stylesheet set/order drifted: {links}. The public base.html "
        "loads tokens → base → components → page; the portal must too."
    )


def test_portal_charts_can_resolve_tokens():
    """Every token manage.css reads WITHOUT an inline fallback must exist
    in tokens.css (a missing token computes invalid → transparent)."""
    import re

    tokens_src = (REPO / "static" / "css" / "tokens.css").read_text()
    defined = set(re.findall(r"^\s*(--[a-z0-9-]+)\s*:", tokens_src, re.M))
    manage_src = (REPO / "static" / "css" / "manage.css").read_text()
    # var(--token) with NO ", fallback" → must be defined
    bare = set(
        re.findall(r"var\((--[a-z0-9-]+)\s*\)", manage_src)
    )
    missing = sorted(bare - defined)
    assert missing == [], (
        f"manage.css reads tokens that don't exist and have no fallback "
        f"(they compute invalid → transparent): {missing}"
    )


def test_seed_demo_enquiry_flag_is_opt_in():
    """The sample-enquiries seeder must stay behind --with-enquiries so
    existing test fixtures stay byte-identical."""
    src = (
        REPO / "apps" / "listings" / "management" / "commands" / "seed_demo.py"
    ).read_text()
    assert '"--with-enquiries"' in src
    assert 'if with_enquiries:' in src


def test_no_template_comment_leaks_on_any_portal_page(db, client):
    """Multi-line {# #} comments leak as raw text (Django's single-line
    syntax) — caught twice in one run (public base.html r73, then the
    portal base.html the VLM caught live). Guard every portal screen."""
    from django.contrib.auth import get_user_model

    get_user_model().objects.create_superuser(
        email="owner@test.com", password="owner-pass-123"
    )
    client.force_login(get_user_model().objects.get(email="owner@test.com"))
    from apps.inquiries.models import Inquiry
    from apps.listings.models import Property

    if Property.objects.exists():
        Inquiry.objects.create(
            property_ref=Property.objects.published().first(),
            name="Leak Guard", email="l@x.com", phone="", message="x",
        )
        detail = Inquiry.objects.first().pk
    else:
        detail = None
    pages = ["/manage/", "/manage/enquiries/", "/manage/site-content/", "/manage/seo/", "/manage/listings/"]
    if detail:
        pages.append(f"/manage/enquiries/{detail}/")
    for url in pages:
        r = client.get(url)
        assert r.status_code == 200, url
        body = r.content.decode()
        assert "{#" not in body, f"template comment leaked on {url}"
        assert "{% comment" not in body, f"raw comment tag on {url}"
