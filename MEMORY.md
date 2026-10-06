# Persistent Memory — Standing User Preferences

> Future sessions/agents: READ THIS FILE FIRST. These are explicit, standing
> instructions from the user. Do not re-ask, do not forget.

## 1. ALWAYS present documents/deliverables IN THIS UI (user instruction, 2026-10-05)

The user was frustrated by deliverables that only existed as file paths / Files-panel
entries. Standing rule for EVERY deliverable (documents, pages, snapshots, reports):

1. **Save the file** to `/home/z/my-project/download/` as usual (Files panel still works).
2. **ALSO make it viewable inside the chat UI**: if the deliverable is HTML/web content,
   serve it on **port 3000** (the sandbox port the Preview Panel proxies), e.g.:
   ```
   cp <file>.html /home/z/my-project/scripts/preview_site/index.html
   nohup python3 -m http.server 3000 --bind 0.0.0.0 --directory /home/z/my-project/scripts/preview_site &
   ```
   then tell the user to look at the **Preview Panel** (right side of the interface,
   "Open in New Tab" button above it) and give the preview link:
   `https://preview-<bot-id>.space-z.ai/` (bot id from the IM gateway session_id).
3. **Non-HTML deliverables** (docx/pdf/xlsx/pptx/png): still save to download/ AND state
   clearly in the reply where the file is; consider rendering an HTML preview of the
   content on port 3000 when practical so the user sees it inline without downloading.
4. Never answer with only a filesystem path. The reply must always include the
   in-UI presentation (preview link / preview panel instruction) plus the file location.

## 2. Project context (Gabriel Homes)

- Django site lives in `/home/z/my-project/gabriel_homes/` (apps: accounts, listings,
  inquiries, core, agents, locations). Tests: 232 pytest / 58 smoke / 46 functional.
- One-click deliverable: `download/gabriel-homes-oneclick.zip` (v3, 29 MB, includes
  redesign photography + Fraunces fonts). Rebuild via `scripts/build_package.sh`,
  verify via `scripts/verify_v3_zip.sh` (18 gates).
- Design language: "Coastal Editorial" — cream/clay/espresso palette, Fraunces display
  serif + Geist text, [ BRACKETED ] mono tags, numbered cards, real photography.
- Single-file home page snapshot: `download/gabriel-homes-homepage.html` (2.2 MB,
  1 style block + 1 script block, all assets base64). Rebuild via
  `scripts/build_single_home.py` (requires dev server curl to /tmp/home_rendered.html).
- Demo accounts: admin@gabrielhomes.co.ke / hello@gabrielhomes.co.ke — password gabriel2026.
