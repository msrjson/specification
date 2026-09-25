# version: 1.0.0 | build: 2026-09-25 | update: 2026-09-25
"""MSR JSON 2.1 is the 2.0 schema plus the fields of RFC 0006, 0008 and 0009, nothing else.

The v2.1 draft once kept only the new fields and dropped every 2.0 constraint, so it
accepted any manifest that had the five top-level keys. These tests pin 2.1 to 2.0,
close every object it declares, and keep the superseded draft identical to 2.1.
"""

import copy
import json
import pathlib

import pytest
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "msr-2.1.json"
SUPERSEDED_DRAFT = ROOT / "schemas" / "msr-2.1-draft.json"
STABLE_SCHEMA = ROOT / "schemas" / "msr-2.0.json"
SCHEMA_URL = "https://msrjson.org/schemas/msr-2.1.json"
EXAMPLES = sorted((ROOT / "examples").glob("*.json"))


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validator():
    return Draft202012Validator(_load(SCHEMA))


@pytest.fixture
def manifest():
    data = _load(ROOT / "examples" / "saas.json")
    data["$schema"] = SCHEMA_URL
    return data


def _errors(validator, data):
    return [e.message for e in validator.iter_errors(data)]


def _strip_rfc_additions(schema):
    """Return the schema with every documented RFC addition removed."""
    stable = _load(STABLE_SCHEMA)
    result = copy.deepcopy(schema)
    for key in ("$id", "title", "description"):
        result[key] = stable[key]
    del result["$defs"]
    props = result["properties"]
    del props["distribution"]
    entity = props["entity"]
    for key in ("media", "category", "subcategories"):
        del entity["properties"][key]
    del entity["dependentRequired"]
    descriptions = entity["properties"]["descriptions"]
    del descriptions["propertyNames"]
    del descriptions["description"]
    for key in ("availability", "requirements"):
        del props["capabilities"]["properties"][key]
    del props["telemetry"]["properties"]["ping_endpoints"]
    return result


def test_schema_is_stable_schema_plus_rfc_additions():
    assert _strip_rfc_additions(_load(SCHEMA)) == _load(STABLE_SCHEMA)


def _open_objects(node, path=""):
    if isinstance(node, dict):
        if "properties" in node and node.get("additionalProperties") is not False:
            yield path
        for key, value in node.items():
            yield from _open_objects(value, f"{path}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _open_objects(value, f"{path}[{index}]")


def test_every_declared_object_is_closed():
    assert list(_open_objects(_load(SCHEMA))) == []


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_reference_manifests_validate_against_2_1(validator, path):
    data = _load(path)
    data["$schema"] = SCHEMA_URL
    assert not _errors(validator, data)


@pytest.mark.parametrize(
    "section", [None, "entity", "capabilities", "telemetry", "protocol", "releases"]
)
def test_unknown_property_is_rejected(validator, manifest, section):
    target = manifest if section is None else manifest.setdefault(section, {})
    target["not_in_the_schema"] = True
    assert any("Additional properties" in e for e in _errors(validator, manifest))


@pytest.mark.parametrize(
    ("section", "field"),
    [
        ("entity", "name"),
        ("entity", "domain"),
        ("protocol", "author"),
        ("releases", "latest"),
        ("capabilities", "deployment"),
    ],
)
def test_stable_required_fields_stay_required(validator, manifest, section, field):
    del manifest[section][field]
    assert any(f"'{field}' is a required property" in e for e in _errors(validator, manifest))


def test_ai_sandbox_without_an_rfc_is_rejected(validator, manifest):
    manifest["capabilities"]["ai_sandbox"] = {"isolation_level": "container"}
    assert _errors(validator, manifest)


def test_superseded_draft_matches_2_1_apart_from_metadata():
    draft, ratified = _load(SUPERSEDED_DRAFT), _load(SCHEMA)
    assert draft["$id"] == "https://msrjson.org/schemas/msr-2.1-draft.json"
    for key in ("$id", "title", "description"):
        draft[key] = ratified[key]
    assert draft == ratified


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_reference_manifests_declare_2_1_and_still_validate_as_2_0(path):
    data = _load(path)
    assert data["$schema"] == SCHEMA_URL
    assert data["protocol"]["version"] == "2.1.0"
    assert not _errors(Draft202012Validator(_load(STABLE_SCHEMA)), data)
