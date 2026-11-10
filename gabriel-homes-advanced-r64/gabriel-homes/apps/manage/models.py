"""Owner portal models (P2-2 Setup Checklist).

Only the OWNER'S OWN progress is stored here. Items the site can verify
by itself (contact details filled in, demo data hidden, first real
listing published) are computed live from the database — see
apps/manage/checklist.py — so the checklist can never drift from
reality. This table exists for the honest remainder: items only the
owner can decide (e.g. "the About page tells my story right").

Rows are never deleted; un-ticking flips ``done`` back and keeps the
audit trail in ``done_at`` / ``updated_at``.
"""
from __future__ import annotations

from django.db import models


class ChecklistItemState(models.Model):
    """Owner-ticked completion state for one manual checklist item."""

    key = models.CharField(max_length=64, unique=True, db_index=True)
    done = models.BooleanField(default=False)
    done_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "checklist item"
        verbose_name_plural = "checklist items"

    def __str__(self) -> str:
        return f"{self.key}: {'done' if self.done else 'open'}"
