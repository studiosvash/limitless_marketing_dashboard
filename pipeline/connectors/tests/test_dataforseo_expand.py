"""Unit tests for the Keyword Explorer expansion parsing/classification (no live HTTP)."""
from pipeline.connectors.dataforseo_keywords import DataForSEOKeywordsConnector as C


def test_classify_match_buckets():
    seed_phrases = ["iv therapy"]
    seed_token_sets = [{"iv", "therapy"}]
    cases = {
        "iv therapy": "exact",
        "what is iv therapy": "questions",       # question word wins over phrase
        "mobile iv therapy": "phrase",            # contiguous seed phrase
        "therapy iv drip": "broad",               # tokens present, not contiguous -> broad
        "vitamin drip clinic": "broad",           # category-relevant (widest net) -> broad, not hidden
    }
    for kw, expected in cases.items():
        assert C._classify_match(kw, seed_phrases, seed_token_sets) == expected, kw


def test_parse_idea_item_maps_shape_and_reverses_monthly():
    item = {
        "keyword": "iv therapy near me",
        "keyword_info": {
            "search_volume": 8100, "cpc": 3.987, "competition_level": "HIGH",
            # newest-first, as DataForSEO returns it
            "monthly_searches": [
                {"year": 2026, "month": 6, "search_volume": 90},
                {"year": 2026, "month": 5, "search_volume": 70},
                {"year": 2026, "month": 4, "search_volume": 50},
            ],
        },
        "keyword_properties": {"keyword_difficulty": 42},
        "search_intent_info": {"main_intent": "transactional"},
        "serp_info": {"serp_item_types": ["organic", "local_pack", "people_also_ask"]},
    }
    row = C._parse_idea_item(item)
    assert row["kw"] == "iv therapy near me"
    assert row["volume"] == 8100
    assert row["kd"] == 42
    assert row["cpc"] == 3.99                       # rounded
    assert row["intent"] == "transactional"         # lowercase, matches intentView
    assert row["monthly"] == [50, 70, 90]           # reversed to oldest->newest
    assert row["serpFeatures"] == ["organic", "local_pack", "people_also_ask"]


def test_parse_idea_item_missing_keyword_returns_none():
    assert C._parse_idea_item({"keyword_info": {"search_volume": 10}}) is None


def test_expand_keywords_empty_seeds_is_error():
    out = C().expand_keywords([], "United States")
    assert out["status"] == "error"
    assert out["rows"] == []


def test_expand_keywords_fetches_and_classifies_related_and_questions_concurrently(monkeypatch):
    c = C()
    c.login = "test"
    c.password = "secret"

    def mock_ideas(seeds, loc, lim):
        return {
            "cost": 0.002,
            "tasks": [{
                "result": [{
                    "items": [
                        {"keyword": "event staffing agency", "keyword_info": {"search_volume": 1200}},
                        {"keyword": "event staffing", "keyword_info": {"search_volume": 5000}}
                    ]
                }]
            }]
        }

    def mock_related(seed, loc, lim):
        return {
            "cost": 0.001,
            "tasks": [{
                "result": [{
                    "items": [
                        {"keyword": "promo staff near me", "keyword_info": {"search_volume": 800}},
                        {"keyword": "event staffing", "keyword_info": {"search_volume": 5000}}
                    ]
                }]
            }]
        }

    def mock_questions(seeds, loc, lim):
        return {
            "cost": 0.001,
            "tasks": [{
                "result": [{
                    "items": [
                        {"keyword": "how much does event staffing cost", "keyword_info": {"search_volume": 150}}
                    ]
                }]
            }]
        }

    monkeypatch.setattr(c, "_fetch_keyword_ideas", mock_ideas)
    monkeypatch.setattr(c, "_fetch_related_keywords", mock_related)
    monkeypatch.setattr(c, "_fetch_keyword_suggestions", mock_questions)

    res = c.expand_keywords(["event staffing"], "United States")
    assert res["status"] == "ok"
    assert res["cost"] == 0.004

    by_kw = {r["kw"]: r["match"] for r in res["rows"]}
    assert by_kw["event staffing"] == "exact"
    assert by_kw["event staffing agency"] == "phrase"
    assert by_kw["promo staff near me"] == "related"
    assert by_kw["how much does event staffing cost"] == "questions"

