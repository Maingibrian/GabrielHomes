"""P1-1 — the public agent pages are retired (single-owner mode).

Loop protocol §4: /agents/ and /agents/<slug>/ must send PERMANENT
redirects to /about/, and no public page chrome (nav / footer) may link
to the old URLs.

The directory/profile view classes and templates stay in the repo
untouched — only routing changed (logged in BRIEF run 5). The run-4
empty-state work on the directory template is preserved in-repo but
publicly unreachable. The owner dashboard's "view public profile" link
now lands on /about/ (acceptable until the /manage/ portal replaces it).
"""
import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db


def _seed():
    call_command("seed_demo", no_images=True, target=80, verbosity=0, i_know_this_is_demo=True)


def test_directory_url_permanently_redirects(client):
    r = client.get("/agents/")
    assert r.status_code == 301
    assert r["Location"] == "/about/"


def test_profile_url_permanently_redirects(client):
    _seed()
    from apps.agents.models import AgencyProfile

    agency = AgencyProfile.objects.public().order_by("pk").first()
    r = client.get(f"/agents/{agency.slug}/")
    assert r.status_code == 301
    assert r["Location"] == "/about/"


def test_unknown_slug_still_redirects(client):
    """RedirectView never touches the DB — old bookmarks 301 whatever the
    slug, including ones that never existed (and demo-hidden agencies,
    which used to 404)."""
    r = client.get("/agents/agency-that-never-existed/")
    assert r.status_code == 301
    assert r["Location"] == "/about/"


def test_redirect_is_followed_to_about(client):
    r = client.get("/agents/", follow=True)
    assert r.status_code == 200
    assert r.request["PATH_INFO"] == "/about/"


def test_no_agent_links_in_public_chrome(client):
    """Nav and footer render on every page — none of it may link to
    /agents/* any more."""
    _seed()
    for url in ["/", "/about/", "/properties/"]:
        html = client.get(url).content.decode()
        assert 'href="/agents' not in html, f"agent link found on {url}"


def test_about_page_has_no_template_comment_leak(client):
    """Run-4's QA guard, now pointed at the redirect target."""
    html = client.get("/about/").content.decode()
    assert "{#" not in html
