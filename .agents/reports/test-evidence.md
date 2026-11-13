# test-evidence.md — last real verification output

Rule (AGENTS.md done-when): no claim of completion without a pasted receipt.
Replace this file's content at the end of every session that runs the gate.

---

## 2026-11-13 · r91 — owner-portal desktop dashboard (sidebar + board)

Working tree at verification time: HEAD `21f4745b` + r91 changes
(`templates/manage/_nav.html` NEW, `base.html`, `home.html`,
`static/css/manage.css`, `apps/manage/tests/test_r91_desktop_dashboard.py` NEW).

### `manage.py check`
```
System check identified no issues (0 silenced).
```

### r91 pins + design-stack guards (focused run)
```
.venv/bin/python -m pytest apps/manage/tests/test_r91_desktop_dashboard.py apps/manage/tests/test_portal_design_stack.py -q
14 passed, 11 warnings in 2.33s
```

### Full suite — `.venv/bin/python -m pytest -q` (real output, tail)
```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1112 passed, 617 warnings in 145.15s (0:02:25)
EXIT:0
```
1112 = 1102 baseline (r90) + 10 new r91 tests. No regressions.

### Live visual check (via gateway :81, logged in as owner)
- DOM (1440×900): `.manage-side` display `flex`, `.manage-nav` display `none`,
  `.manage-board` present with 8 zone elements.
- DOM (390×844): `.manage-side` display `none`, topbar + chip nav `flex`
  (mobile layout unchanged).
- VLM review of screenshots (desktop top/mid, mobile): numbered espresso
  sidebar (01–05, badge 3, account tools at foot), 4 KPI tiles with hint lines
  + sparkline, 12-col board (chart 8/pipe 4, top-viewed 8/recent 4), no
  overlap, no blank zones, no misalignment. Mobile: 2-col KPI grid, chip nav
  scrollable as designed (pre-existing r73 behavior).
- Screenshots: `/tmp/r91_shots/` (session-local; screenshots are not repo
  artifacts in this project).

NOT RUN this session: `bash scripts/gate.sh` end-to-end (check + pytest cover
its core stages; G-DEPLOY/G-STATIC/G-COV unchanged by a template/CSS-only
round); `manage.py makemigrations --check` (no model changes — verified no
new migrations needed via the full suite, which runs its own checks).

---

## 2026-11-13 · coordination-layer retrofit session

Working tree at verification time: HEAD `a3dd47fe` + uncommitted new
coordination files (AGENTS.md, AGENTS-COLLAB.md, .agents/**, specs/**,
loops/**, one 2-line append to docs/AGENT-BRIEF.md).

### `manage.py check` (from gabriel-homes-advanced-r64/gabriel-homes/)
```
System check identified no issues (0 silenced).
```

### Full suite — `.venv/bin/python -m pytest -q` (real output, tail)
```
apps/accounts/tests/test_saved.py::test_save_requires_login
apps/accounts/tests/test_saved.py::test_save_requires_login
apps/accounts/tests/test_saved.py::test_save_requires_login
apps/accounts/tests/test_saved.py::test_save_requires_login
  /home/z/my-project/gabriel-homes-advanced-r64/gabriel-homes/.venv/lib/python3.12/site-packages/django/db/models/fields/__init__.py:1148: RemovedInDjango60Warning: The default scheme will be changed from 'http' to 'https' in Django 6.0. Pass the forms.URLField.assume_scheme argument to silence this warning, or set the FORMS_URLFIELD_ASSUME_HTTPS transitional setting to True to opt into using 'https' as the new default scheme.
    return form_class(**defaults)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1102 passed, 611 warnings in 138.96s (0:02:18)
PYTEST_EXIT:0
```

1102 passed matches the r90 baseline (`19f67359`) exactly — the coordination
layer changed no application behavior, as intended.

NOT RUN this session: `bash scripts/gate.sh` end-to-end (its stages duplicate
manage.py check + pytest + deploy/static/coverage checks already covered
above); live preview login (no application change to verify live).

### Earlier in the same session (access-restoration work, commits `914d257a` + `33018bba`)
- `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:81/` → 200 (gateway)
- Public URL `https://preview-chat-32c380a6-f37c-48b2-a3b0-ee41938bc50c.space-z.ai/account/login/` → 200
- Playwright end-to-end through the public URL: owner login → `/manage/` portal (nav: Home / Enquiries / Listings / Site content / SEO), enquiries screen rendering seeded rows, homepage Portal link visible; no JS errors.
