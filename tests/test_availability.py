# version: 1.2.0 | build: 2026-09-18 | update: 2026-09-25
"""RFC-0006: geographic and language availability, in the MSR JSON 2.1 schema.

The block lives only in 2.1. Stable 2.0 manifests are untouched, and the
2.0 schema must keep rejecting the block, because adding a property to a closed
object would change what validates.
"""

import copy
import json
import pathlib

import pytest
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "msr-2.1.json"
STABLE_SCHEMA = ROOT / "schemas" / "msr-2.0.json"

AVAILABILITY = {
    "regions": ["019", "150"],
    "countries": ["AO", "MZ"],
    "excluded_countries": ["CU"],
    "languages": ["pt-BR", "en", "es-419", "zh-Hant-TW"],
    "support_languages": ["pt-BR", "en"],
    "currencies": ["BRL", "EUR", "USD"],
    "data_residency": ["BR", "150"],
}


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validator():
    schema = _load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.fixture
def manifest():
    data = _load(ROOT / "examples" / "saas.json")
    data["$schema"] = "https://msrjson.org/schemas/msr-2.1.json"
    data["capabilities"]["availability"] = copy.deepcopy(AVAILABILITY)
    return data


def _errors(validator, data):
    return [e.message for e in validator.iter_errors(data)]


def test_full_availability_block_validates(validator, manifest):
    assert not _errors(validator, manifest)


def test_worldwide_is_declared_with_region_001(validator, manifest):
    manifest["capabilities"]["availability"] = {"regions": ["001"]}
    assert not _errors(validator, manifest)


def test_manifest_without_availability_still_validates(validator, manifest):
    del manifest["capabilities"]["availability"]
    assert not _errors(validator, manifest)


@pytest.mark.parametrize(
    "field, value",
    [
        ("regions", ["999"]),          # not an M49 region
        ("regions", ["076"]),          # M49 country code (Brazil), not a region
        ("regions", ["Europe"]),       # names are not codes
        ("countries", ["br"]),         # ISO 3166-1 is uppercase
        ("countries", ["BRA"]),        # alpha-3 is not accepted
        ("excluded_countries", ["150"]),
        ("languages", ["pt_BR"]),      # BCP 47 uses a hyphen
        ("languages", ["Portuguese"]),
        ("data_residency", ["eu"]),
        ("support_languages", ["pt_BR"]),
        ("support_languages", []),
        ("currencies", ["brl"]),       # ISO 4217 is uppercase
        ("currencies", ["R$"]),        # symbols are not codes
        ("currencies", ["EURO"]),
        ("currencies", ["USD", "USD"]),
        ("data_residency", ["999"]),
        ("regions", []),               # an empty list declares nothing
        ("languages", ["en", "en"]),
    ],
)
def test_invalid_values_are_rejected(validator, manifest, field, value):
    manifest["capabilities"]["availability"][field] = value
    assert _errors(validator, manifest), f"{field}={value!r} should not validate"


def test_eu_is_accepted_for_data_residency(validator, manifest):
    """EU is ISO 3166-1 exceptionally reserved and a CLDR region; M49 150 is
    all of Europe, which is not the same legal perimeter for data protection."""
    manifest["capabilities"]["availability"]["data_residency"] = ["EU"]
    assert not _errors(validator, manifest)


def test_unknown_availability_key_is_rejected(validator, manifest):
    manifest["capabilities"]["availability"]["continents"] = ["Europe"]
    assert any("Additional properties" in m for m in _errors(validator, manifest))


def test_empty_availability_block_is_rejected(validator, manifest):
    manifest["capabilities"]["availability"] = {}
    assert _errors(validator, manifest)


def test_description_keys_must_be_language_tags(validator, manifest):
    manifest["entity"]["descriptions"]["pt-BR"] = {"summary": "Resumo."}
    assert not _errors(validator, manifest)
    manifest["entity"]["descriptions"]["portuguese"] = {"summary": "Resumo."}
    assert _errors(validator, manifest)


def test_stable_schema_still_rejects_the_block(manifest):
    """2.0 is closed: the block cannot leak into stable manifests."""
    stable = Draft202012Validator(_load(STABLE_SCHEMA))
    manifest["$schema"] = "https://msrjson.org/schemas/msr-2.0.json"
    assert any("Additional properties" in m for m in _errors(stable, manifest))
