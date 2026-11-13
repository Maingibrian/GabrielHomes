# test-evidence.md — last real verification output

Rule (AGENTS.md done-when): no claim of completion without a pasted receipt.
Replace this file's content at the end of every session that runs the gate.

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
