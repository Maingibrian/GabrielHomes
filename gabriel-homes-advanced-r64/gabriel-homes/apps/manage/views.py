"""Owner portal views — /manage/.

The portal is the owner's own workspace, deliberately separate from both
the public site chrome and the retired agent dashboards:

  * The access gate lives HERE (``OwnerRequiredMixin``), not in
    apps.agents — the portal must never depend on the agents app, which
    only survives as a developer-side dashboard until /manage/ absorbs it
    (P3). The agents app keeps its own copy; this one is the portal's.
  * One primary action per screen (protocol §5): the home screen's
    primary action is the checklist's exact next step.
  * Plain language, mobile-first, cream/espresso tokens only.
"""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import FormView, TemplateView, View

from . import checklist
from .forms import SiteContentForm
from .models import ChecklistItemState
from apps.core.models import BrandSettings


class OwnerRequiredMixin:
    """Only the site owner (superuser) may pass.

    Unauthenticated visitors are redirected to login (honours
    settings.LOGIN_URL and ?next=). Authenticated non-owners — agents,
    regular users — get 403, never a redirect loop.

    (Deliberately NOT using LoginRequiredMixin as a base any more: the
    P2-2 toggle view is a plain View, so the gate is self-contained
    instead of tied to class-based-view dispatch ordering.)
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login

            return redirect_to_login(request.get_full_path())
        if not request.user.is_superuser:
            raise PermissionDenied("This area is for the site owner only.")
        return super().dispatch(request, *args, **kwargs)


class PortalHomeView(OwnerRequiredMixin, TemplateView):
    """Portal home: counts + Setup Checklist (P2-2)."""

    template_name = "manage/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["body_class"] = "page-manage"
        ctx["counts"] = checklist.counts()
        ctx["checklist"] = checklist.build_checklist()
        return ctx


class ChecklistToggleView(OwnerRequiredMixin, View):
    """Owner ticks / un-ticks a MANUAL checklist item (POST only).

    Derived items refuse to be toggled — their state is computed from
    the database, and the owner ticking "publish a listing" by hand
    would not make a listing exist.
    """

    def post(self, request, key: str):
        if key not in checklist.MANUAL_KEYS:
            raise Http404("No manual checklist item with that key.")
        spec = next(i for i in checklist.REGISTRY if i.key == key)
        state, _created = ChecklistItemState.objects.get_or_create(key=key)
        state.done = not state.done
        state.done_at = timezone.now() if state.done else None
        state.save(update_fields=["done", "done_at", "updated_at"])
        if state.done:
            messages.success(request, f"Done: {spec.label}. Well paced.")
        else:
            messages.info(request, f"Reopened: {spec.label}.")
        return redirect("manage:home")


class SiteContentView(OwnerRequiredMixin, FormView):
    """Small owner-editable CMS for public contact details and homepage copy."""

    template_name = "manage/site_content.html"
    form_class = SiteContentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = BrandSettings.load()
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Site content saved. The public site is updated.")
        return redirect("manage:site_content")
