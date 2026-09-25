# version: 1.1.0 | build: 2026-09-21 | update: 2026-09-25
"""RFC-0008: Media assets, package managers, execution requirements & push-ping in MSR JSON 2.1."""

import copy
import json
import pathlib

import pytest
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "msr-2.1.json"
STABLE_SCHEMA = ROOT / "schemas" / "msr-2.0.json"

MEDIA_BLOCK = {
    "icon": {
        "svg": "https://example.com/assets/icon.svg",
        "png_256": "https://example.com/assets/icon-256.png",
    },
    "screenshots": [
        {
            "url": "https://example.com/assets/screen-main.webp",
            "title": "Main Dashboard",
            "width": 1920,
            "height": 1080,
            "lang": "pt-BR",
        }
    ],
    "video_demo_url": "https://example.com/demo.mp4",
}

DISTRIBUTION_BLOCK = {
    "package_managers": {
        "pypi": "my-pkg",
        "npm": "@org/my-pkg",
        "homebrew": "my-tool",
        "docker": "org/my-tool",
    },
    "app_stores": {
        "google_play": "com.example.app",
        "apple_app_store": "id1234567890",
    },
}

REQUIREMENTS_BLOCK = {
    "architectures": ["x86_64", "arm64"],
    "operating_systems": [
        {"os": "linux", "min_kernel": "5.15"},
        {"os": "darwin", "min_version": "13.0"},
        {"os": "windows", "min_version": "10.0.19041"},
    ],
    "hardware": {
        "min_ram_mb": 512,
        "recommended_ram_mb": 2048,
        "min_storage_mb": 100,
        "gpu": {
            "required": False,
            "min_vram_mb": 4096,
        },
    },
}


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validator():
    schema = _load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.fixture(scope="module")
def stable_validator():
    schema = _load(STABLE_SCHEMA)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.fixture
def base_manifest():
    data = _load(ROOT / "examples" / "saas.json")
    data["$schema"] = "https://msrjson.org/schemas/msr-2.1.json"
    return data


def _errors(validator, data):
    return [e.message for e in validator.iter_errors(data)]


def test_schema_itself_is_valid_draft_2020_12():
    schema = _load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    assert schema["$id"] == "https://msrjson.org/schemas/msr-2.1.json"


def test_manifest_with_full_v21_rfc0008_features_validates(
    validator, base_manifest
):
    manifest = copy.deepcopy(base_manifest)
    manifest["entity"]["media"] = copy.deepcopy(MEDIA_BLOCK)
    manifest["distribution"] = copy.deepcopy(DISTRIBUTION_BLOCK)
    manifest["capabilities"]["requirements"] = copy.deepcopy(REQUIREMENTS_BLOCK)
    manifest["telemetry"]["ping_endpoints"] = ["https://mysoftrank.com/api/v1/ping"]

    errors = _errors(validator, manifest)
    assert not errors, f"Unexpected errors: {errors}"


def test_screenshots_require_url(validator, base_manifest):
    manifest = copy.deepcopy(base_manifest)
    manifest["entity"]["media"] = {"screenshots": [{"title": "Missing URL"}]}
    errors = _errors(validator, manifest)
    assert any("'url' is a required property" in e for e in errors)


def test_invalid_architecture_is_rejected(validator, base_manifest):
    manifest = copy.deepcopy(base_manifest)
    manifest["capabilities"]["requirements"] = {"architectures": ["quantum-cpu-9000"]}
    errors = _errors(validator, manifest)
    assert any("quantum-cpu-9000" in e for e in errors)


def test_negative_ram_is_rejected(validator, base_manifest):
    manifest = copy.deepcopy(base_manifest)
    manifest["capabilities"]["requirements"] = {"hardware": {"min_ram_mb": -512}}
    errors = _errors(validator, manifest)
    assert any("-512 is less than the minimum of 0" in e for e in errors)


def test_stable_schema_rejects_rfc0008_fields(stable_validator, base_manifest):
    """MSR JSON 2.0 schema must reject distribution, media, requirements."""
    manifest = copy.deepcopy(base_manifest)
    manifest["$schema"] = "https://msrjson.org/schemas/msr-2.0.json"
    manifest["distribution"] = copy.deepcopy(DISTRIBUTION_BLOCK)
    manifest["entity"]["media"] = copy.deepcopy(MEDIA_BLOCK)
    manifest["capabilities"]["requirements"] = copy.deepcopy(REQUIREMENTS_BLOCK)

    errors = _errors(stable_validator, manifest)
    assert len(errors) >= 3, f"Expected 2.0 to reject 2.1 fields, but got: {errors}"


@pytest.mark.parametrize(
    "field", ["icon", "screenshot", "video", "ping_endpoint"]
)
def test_rfc0008_urls_must_use_https(validator, base_manifest, field):
    manifest = copy.deepcopy(base_manifest)
    plain = "http://example.com/asset"
    if field == "icon":
        manifest["entity"]["media"] = {"icon": {"svg": plain}}
    elif field == "screenshot":
        manifest["entity"]["media"] = {"screenshots": [{"url": plain}]}
    elif field == "video":
        manifest["entity"]["media"] = {"video_demo_url": plain}
    else:
        manifest["telemetry"]["ping_endpoints"] = [plain]
    assert any("does not match '^https://'" in e for e in _errors(validator, manifest))
