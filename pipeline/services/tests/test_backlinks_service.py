"""Unit tests for the Backlinks service's pure shaping helpers (no live HTTP)."""
from pipeline.services import backlinks_service as bl


def test_as_scales_1000_to_100_and_clamps():
    assert bl._as(1000) == 100
    assert bl._as(100) == 10       # DataForSEO 0-1000 -> 0-100
    assert bl._as(0) == 0
    assert bl._as(None) == 0
    assert bl._as("bad") == 0
    assert bl._as(5000) == 100     # clamped


def test_classify_anchor():
    assert bl._classify_anchor("", "fusehealth") == "Empty"
    assert bl._classify_anchor("fusehealth.com", "fusehealth") == "Branded"
    assert bl._classify_anchor("click here", "fusehealth") == "Generic"
    assert bl._classify_anchor("best iv therapy clinic", "fusehealth") == "Keyword"


def test_clean_domain_strips_scheme_and_scdomain():
    assert bl._clean_domain("https://fusehealth.com/") == "fusehealth.com"
    assert bl._clean_domain("sc-domain:fusehealth.com") == "fusehealth.com"


def test_empty_payload_has_all_keys():
    p = bl.empty_backlinks_payload()
    for key in ("summary", "months", "types", "asBuckets", "anchors", "refDomains",
                "links", "competitors", "gapDomains"):
        assert key in p
    assert p["summary"]["backlinks"] == 0
