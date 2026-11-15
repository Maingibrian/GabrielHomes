"""Tests for the owner's real listing import + video support + agent spread."""
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import Client, TestCase, override_settings

from apps.listings.models import Property

TINY_JPG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xd9"
)
FAKE_MP4 = b"\x00\x00\x00\x18ftypmp42fake-video-payload"


class ImportRealListingTests(TestCase):
    def _stage(self, root):
        src = root / "real-listing-src"
        src.mkdir(parents=True)
        for i in (1, 2):
            (src / f"real-{i:02d}.jpg").write_bytes(TINY_JPG)
        (src / "real-tour.mp4").write_bytes(FAKE_MP4)
        return src

    def _import(self, root):
        """Seed + import with MEDIA_ROOT pointed at a throwaway dir.

        import_real_listing copies media into settings.MEDIA_ROOT using fixed
        names (nyali-real-01.jpg, nyali-real-tour.mp4). Without this override,
        a test run would OVERWRITE the live listing's real photos and video
        with tiny test stubs (this actually happened once)."""
        src = self._stage(root / "src")
        media = root / "media"
        media.mkdir()
        with override_settings(MEDIA_ROOT=str(media)):
            call_command("seed_demo", no_images=True, i_know_this_is_demo=True, verbosity=0)
            call_command("import_real_listing", src=str(src), verbosity=0)

    def test_import_creates_featured_listing_with_video(self):
        with TemporaryDirectory() as tmp:
            self._import(Path(tmp))

        p = Property.objects.get(slug="modern-beachfront-apartment-nyali")
        self.assertTrue(p.is_featured)
        self.assertEqual(p.status, Property.Status.PUBLISHED)
        self.assertEqual(p.images.count(), 2)
        self.assertTrue(p.images.filter(is_cover=True).exists())
        self.assertIn("property-videos/", p.video.name)
        self.assertEqual(p.agent.slug, "gabriel-homes")

    def test_detail_page_renders_video_block(self):
        with TemporaryDirectory() as tmp:
            self._import(Path(tmp))

        p = Property.objects.get(slug="modern-beachfront-apartment-nyali")
        r = Client().get(p.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertIn("<video", html)
        # r103: the bracket "[ VIDEO TOUR ]" label retired with the other
        # dev-syntax labels; the eyebrow is editorial copy now, uppercased
        # by CSS (text-transform), not by literal brackets in the markup.
        self.assertNotIn("[ VIDEO TOUR ]", html)
        self.assertIn("detail-video__tag", html)

    def test_reimport_is_idempotent(self):
        with TemporaryDirectory() as tmp:
            self._import(Path(tmp))
            media_root = Path(tmp) / "media"
            # Second import with the SAME isolated MEDIA_ROOT: idempotency.
            with override_settings(MEDIA_ROOT=str(media_root)):
                call_command("import_real_listing", src=str(Path(tmp) / "src"), verbosity=0)

        self.assertEqual(
            Property.objects.filter(slug="modern-beachfront-apartment-nyali").count(),
            1,
        )
        p = Property.objects.get(slug="modern-beachfront-apartment-nyali")
        self.assertEqual(p.images.count(), 2)


class SeedAgentSpreadTests(TestCase):
    """Every agent owns a DISJOINT slice of listings (round-robin, not random)."""

    def test_each_agent_has_unique_listings(self):
        call_command("seed_demo", no_images=True, i_know_this_is_demo=True, verbosity=0)
        from apps.agents.models import AgencyProfile

        agencies = list(AgencyProfile.objects.all())
        self.assertGreaterEqual(len(agencies), 2)

        per_agent = {a.slug: set() for a in agencies}
        for p in Property.objects.iterator():
            per_agent[p.agent.slug].add(p.slug)

        seen = set()
        for slug, props in per_agent.items():
            self.assertTrue(props, f"{slug} has no listings")
            overlap = seen & props
            self.assertEqual(overlap, set(), f"{slug} shares listings: {overlap}")
            seen |= props

        counts = [len(v) for v in per_agent.values()]
        self.assertLessEqual(max(counts) - min(counts), 1)
