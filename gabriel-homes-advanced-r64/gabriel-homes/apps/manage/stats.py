"""Dashboard stats (r73, BACKEND-PLAN 1B) — every number on the portal
home screen, computed from the database, demo-switch aware.

Design rules (BACKEND-PLAN): no invented numbers, designed empty
states, plain language. Graphs are CSS bars rendered by the template —
this module only supplies the data shapes:

    per_day      -> [{date, count, pct}]  30 entries, zero-filled
    by_status    -> [{key, label, count, pct}]  the five pipeline states
    top_viewed   -> [{title, url, views, pct}]  max 5, views > 0
    recent       -> the five newest non-spam enquiries
    totals       -> {views, enquiries_30d}
"""
from __future__ import annotations

from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.core.models import SiteSetting
from apps.inquiries.models import Inquiry
from apps.listings.models import Property

DAYS = 30


def _visible_inquiries():
    """Non-spam enquiries; sample rows vanish with the demo switch."""
    qs = Inquiry.objects.filter(honeypot="")
    if SiteSetting.demo_hidden():
        qs = qs.exclude(is_demo=True)
    return qs


def dashboard_stats() -> dict:
    today = timezone.localdate()
    start = today - timedelta(days=DAYS - 1)
    start_dt = timezone.make_aware(
        timezone.datetime(start.year, start.month, start.day)
    )

    qs = _visible_inquiries()

    # --- enquiries per day, zero-filled across the whole window ---
    counts_by_day = dict(
        qs.filter(created_at__gte=start_dt)
        .annotate(day=TruncDate("created_at"))
        .values_list("day")
        .annotate(c=Count("pk"))
        .values_list("day", "c")
    )
    per_day = []
    for offset in range(DAYS):
        day = start + timedelta(days=offset)
        per_day.append({"date": day, "count": counts_by_day.get(day, 0)})
    peak = max((d["count"] for d in per_day), default=0)
    for d in per_day:
        # 8% floor keeps a visible hairline on quiet days; 0 stays 0.
        d["pct"] = 100 if peak == 0 else max(round(d["count"] * 100 / peak), 8 if d["count"] else 0)

    # --- the five pipeline states, in workflow order ---
    by_status = []
    for value, label in Inquiry.Status.choices:
        by_status.append(
            {"key": value, "label": label, "count": 0, "pct": 0}
        )
    status_counts = dict(
        qs.values_list("status").annotate(c=Count("pk"))
    )
    total_all = sum(status_counts.values())
    for row in by_status:
        row["count"] = status_counts.get(row["key"], 0)
        row["pct"] = round(row["count"] * 100 / total_all) if total_all else 0

    # --- most-viewed live listings (max 5, only real interest) ---
    listing_qs = Property.objects.published()  # honours the demo switch
    top = list(
        listing_qs.filter(views_count__gt=0)
        .order_by("-views_count")[:5]
        .values("title", "slug", "pk", "views_count")
    )
    top_peak = top[0]["views_count"] if top else 0
    top_viewed = [
        {
            "title": t["title"],
            "url": f"/listing/{t['slug']}-{t['pk']}/",
            "views": t["views_count"],
            "pct": round(t["views_count"] * 100 / top_peak) if top_peak else 0,
        }
        for t in top
    ]

    return {
        "per_day": per_day,
        "by_status": by_status,
        "top_viewed": top_viewed,
        "recent": list(qs.select_related("property_ref").order_by("-created_at")[:5]),
        "totals": {
            "views": listing_qs.aggregate(v=Sum("views_count"))["v"] or 0,
            "enquiries_30d": sum(d["count"] for d in per_day),
            "enquiries": qs.count(),
        },
    }


def new_enquiry_count() -> int:
    """Badge count for the nav chip — New, non-spam, demo-aware."""
    return _visible_inquiries().filter(status=Inquiry.Status.NEW).count()
