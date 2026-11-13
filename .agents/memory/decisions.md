# decisions.md — rejected approaches ("We tried X. It failed because Y. Do not propose X again.")

Every entry is traceable to a commit or an in-repo decision record. Append-only.

- We tried keying the enquiry rate limiter on raw `X-Forwarded-For`. It failed because the first XFF entry is client-controlled, so an attacker rotated buckets and got 10 enquiries instead of 3. Do not propose raw XFF again. (`19f67359`; apps/core/clientip.py, defect D-RL)
- We tried keeping the demo-photo pools on disk only (untracked media). It failed because every sandbox recycle wiped them and the re-seed fell back to Pillow gradient cards — the "cards are back" regression, three times. Do not propose untracking `media/demo-photos/` again. (`6534a273`, r57)
- We tried verifying the preview through localhost only. It failed because the public gateway chain delivers different Host headers, so the DisallowedHost 400 shipped masked. Do not propose localhost-only verification again. (`33018bba`)
- We tried a band-sized masked palm-parallax layer (1280x14000 re-rastered every drift frame). It failed because it cost 59ms average frames (jank at 4x throttle); the viewport-sticky box paints the same at 1/17th raster. Do not propose full-band raster layers again. (`86c7a4e9`, r85)
- We tried an ocean photo on the map deck. It failed because the scrim and market cards clashed against it (vision-confirmed); the deck now repeats the band's palm tile under a cream veil. Do not propose the ocean photo again. (`a0263632`, r88)
- We tried Google Maps (API key, billing). It failed because the owner required a no-charge option; the Cloud dependency was removed. Do not propose keyed/paid map services again. (docs/DECISIONS.md, 2026-10-29)
- We tried public OSM raster tiles + an external renderer CDN. It failed because the preview blocked both hosts; the map now runs self-hosted MapLibre GL with OpenFreeMap's positron style. Do not propose external map CDNs again. (docs/DECISIONS.md, 2026-10-29)
- We tried `django-csp` for the Content-Security-Policy header. It failed because one header needed one dict-free policy string with no new dependency to audit; the custom `apps.core.middleware.ContentSecurityPolicyMiddleware` does it. Do not propose django-csp again. (docs/DECISIONS.md, S10)
