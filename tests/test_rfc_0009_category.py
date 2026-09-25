# version: 1.0.0 | build: 2026-09-25 | update: 2026-09-25
"""RFC-0009: entity category and subcategories in MSR JSON 2.1, and the category taxonomy."""

import copy
import json
import pathlib
import re

import pytest
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "msr-2.1.json"
STABLE_SCHEMA = ROOT / "schemas" / "msr-2.0.json"
TAXONOMY = ROOT / "taxonomy" / "categories.json"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validator():
    return Draft202012Validator(_load(SCHEMA))


@pytest.fixture(scope="module")
def stable_validator():
    return Draft202012Validator(_load(STABLE_SCHEMA))


@pytest.fixture(scope="module")
def taxonomy():
    return _load(TAXONOMY)


@pytest.fixture
def base_manifest():
    data = _load(ROOT / "examples" / "saas.json")
    data["$schema"] = "https://msrjson.org/schemas/msr-2.1.json"
    return data


def _errors(validator, data):
    return [e.message for e in validator.iter_errors(data)]


def _with_entity(manifest, **fields):
    result = copy.deepcopy(manifest)
    result["entity"].update(fields)
    return result


def test_category_and_subcategories_validate(validator, base_manifest):
    manifest = _with_entity(
        base_manifest,
        category="funeral-management",
        subcategories=["erp", "point-of-sale"],
    )
    assert not _errors(validator, manifest)


def test_category_alone_validates(validator, base_manifest):
    manifest = _with_entity(base_manifest, category="crm")
    assert not _errors(validator, manifest)


@pytest.mark.parametrize(
    "value",
    ["Funeral-Management", "funeral_management", "-crm", "crm-", "crm--suite", ""],
)
def test_category_must_be_a_slug(validator, base_manifest, value):
    manifest = _with_entity(base_manifest, category=value)
    assert _errors(validator, manifest)


def test_category_longer_than_64_is_rejected(validator, base_manifest):
    manifest = _with_entity(base_manifest, category="a" * 65)
    assert any("is too long" in e for e in _errors(validator, manifest))


def test_more_than_five_subcategories_is_rejected(validator, base_manifest):
    manifest = _with_entity(
        base_manifest,
        category="erp",
        subcategories=["crm", "cms", "vpn", "ides", "rendering", "messaging"],
    )
    assert any("is too long" in e for e in _errors(validator, manifest))


def test_duplicate_subcategories_are_rejected(validator, base_manifest):
    manifest = _with_entity(base_manifest, category="erp", subcategories=["crm", "crm"])
    assert any("non-unique" in e for e in _errors(validator, manifest))


def test_empty_subcategories_are_rejected(validator, base_manifest):
    manifest = _with_entity(base_manifest, category="erp", subcategories=[])
    assert _errors(validator, manifest)


def test_subcategories_require_category(validator, base_manifest):
    manifest = _with_entity(base_manifest, subcategories=["crm"])
    assert any("'category' is a dependency" in e for e in _errors(validator, manifest))


def test_stable_schema_rejects_category(stable_validator, base_manifest):
    manifest = _with_entity(base_manifest, category="crm")
    manifest["$schema"] = "https://msrjson.org/schemas/msr-2.0.json"
    assert _errors(stable_validator, manifest)


def test_taxonomy_slugs_are_unique_sorted_and_schema_valid(taxonomy):
    slugs = [c["slug"] for c in taxonomy["categories"]]
    pattern = re.compile(
        _load(SCHEMA)["properties"]["entity"]["properties"]["category"]["pattern"]
    )
    assert slugs == sorted(set(slugs))
    assert all(pattern.fullmatch(s) and len(s) <= 64 for s in slugs)


def test_taxonomy_entries_carry_a_name(taxonomy):
    assert re.fullmatch(r"\d+\.\d+\.\d+", taxonomy["version"])
    assert all(set(c) == {"slug", "name"} and c["name"] for c in taxonomy["categories"])


def test_taxonomy_contains_the_first_adopter_category(taxonomy):
    assert "funeral-management" in {c["slug"] for c in taxonomy["categories"]}
