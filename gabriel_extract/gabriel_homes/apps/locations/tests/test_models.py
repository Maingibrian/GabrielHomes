"""Tests for the Location tree (apps.locations)."""
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.locations.models import Location

pytestmark = pytest.mark.django_db


def _make_tree():
    """county > area > neighbourhood, returns (county, area, leaf)."""
    county = Location.objects.create(name="Mombasa", level=Location.Level.COUNTY)
    area = Location.objects.create(name="Nyali", parent=county, level=Location.Level.AREA)
    leaf = Location.objects.create(
        name="Nyali Centre", parent=area, level=Location.Level.NEIGHBOURHOOD,
        lat=Decimal("-1.257000"), lng=Decimal("36.803000"),
    )
    return county, area, leaf


def test_save_auto_slugs_and_derives_level():
    county = Location.objects.create(name="Nairobi")  # no level given
    assert county.slug == "nairobi"
    assert county.level == Location.Level.COUNTY

    area = Location.objects.create(name="Westlands", parent=county)
    assert area.level == Location.Level.AREA

    leaf = Location.objects.create(name="Westlands Central", parent=area)
    assert leaf.level == Location.Level.NEIGHBOURHOOD


def test_unique_slug_per_parent():
    county = Location.objects.create(name="Mombasa", level=Location.Level.COUNTY)
    Location.objects.create(name="Nyali", parent=county, level=Location.Level.AREA)
    # Same slug, same parent -> should collide
    with pytest.raises(Exception):
        Location.objects.create(name="Nyali", parent=county, level=Location.Level.AREA)


def test_full_path_joins_ancestors():
    county, area, leaf = _make_tree()
    assert county.full_path() == "Mombasa"
    assert area.full_path() == "Mombasa > Nyali"
    assert leaf.full_path() == "Mombasa > Nyali > Nyali Centre"


def test_get_descendants_returns_all_levels_below():
    county, area, leaf = _make_tree()
    # Plus a second area under the same county
    area2 = Location.objects.create(name="Bamburi", parent=county, level=Location.Level.AREA)
    leaf2 = Location.objects.create(name="Bamburi Mwisho", parent=area2, level=Location.Level.NEIGHBOURHOOD)

    desc_pks = set(county.get_descendants().values_list("pk", flat=True))
    assert desc_pks == {area.pk, leaf.pk, area2.pk, leaf2.pk}

    desc_of_area = set(area.get_descendants().values_list("pk", flat=True))
    assert desc_of_area == {leaf.pk}

    desc_of_leaf = set(leaf.get_descendants().values_list("pk", flat=True))
    assert desc_of_leaf == set()


def test_get_descendants_include_self():
    county, area, leaf = _make_tree()
    pks = set(county.get_descendants(include_self=True).values_list("pk", flat=True))
    assert county.pk in pks


def test_get_ancestors_walks_up():
    county, area, leaf = _make_tree()
    chain = leaf.get_ancestors(include_self=True)
    assert [loc.name for loc in chain] == ["Mombasa", "Nyali", "Nyali Centre"]


def test_is_leaf():
    county, area, leaf = _make_tree()
    assert leaf.is_leaf is True
    assert county.is_leaf is False
