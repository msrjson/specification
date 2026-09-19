"""Regression guards for the registry-security requirements in RFC 0007."""

from pathlib import Path


RFC = Path(__file__).parents[1] / "rfc" / "rfc-0007.html"


def test_rfc_0007_requires_rebinding_and_response_isolation_controls():
    source = RFC.read_text(encoding="utf-8")
    for requirement in (
        "DNS Rebinding Resistance",
        "Response Isolation",
        "after decompression",
        "duplicate-key detection",
        "authorization,",
        "cookies",
        "::ffff:0:0/96",
    ):
        assert requirement in source


def test_rfc_0007_distinguishes_claims_from_independent_verification():
    source = RFC.read_text(encoding="utf-8")
    assert "publisher claim, not proof" in source
    assert "MUST downgrade" in source
    assert "failed verification" in source
