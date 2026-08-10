"""GA4 returns metric values as STRINGS, and a count is not always spelled like an integer.

`conversions` is a floating-point metric in the Data API (partial/weighted conversion credit is
real), so the same property that answers "3" one day can answer "3.0" the next. `int("3.0")`
raises ValueError. Two of the three normalizers in ga4.py already wrapped it in `float()`;
`_normalize_offsite` did not, and it is not guarded -- an exception there escapes `fetch()` and
takes the entire GA4 sync down, including the seo_daily and campaign reports that had already
been paid for.
"""
from datetime import date

from django.test import SimpleTestCase

from pipeline.connectors.ga4 import GA4Connector


class _Value:
    def __init__(self, value):
        self.value = value


class _Row:
    def __init__(self, dimensions, metrics):
        self.dimension_values = [_Value(d) for d in dimensions]
        self.metric_values = [_Value(m) for m in metrics]


class _Response:
    def __init__(self, rows):
        self.rows = rows


class OffsiteNormalizerNumberTests(SimpleTestCase):
    def test_a_float_shaped_conversion_count_does_not_raise(self):
        resp = _Response([
            # date, channel, source | sessions, conversions, engagementRate, totalRevenue
            _Row(["20260605", "Referral", "Example.com"], ["120", "3.0", "0.5", "10.5"]),
        ])
        records = GA4Connector._normalize_offsite(GA4Connector.__new__(GA4Connector), resp,
                                                  "fusehealth.com")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["conversions"], 3)
        self.assertEqual(records[0]["date"], date(2026, 6, 5))
        self.assertEqual(records[0]["sessions"], 120)
        self.assertEqual(records[0]["engaged_sessions"], 60)
        self.assertEqual(records[0]["revenue"], 10.5)
        # sessionSource is a host; it is stored lowercased so the platform map can match it.
        self.assertEqual(records[0]["source"], "example.com")

    def test_an_empty_metric_string_is_zero_not_a_crash(self):
        resp = _Response([
            _Row(["20260605", "Referral", "example.com"], ["", "", "0", ""]),
        ])
        records = GA4Connector._normalize_offsite(GA4Connector.__new__(GA4Connector), resp,
                                                  "fusehealth.com")
        self.assertEqual(records[0]["sessions"], 0)
        self.assertEqual(records[0]["conversions"], 0)
        self.assertEqual(records[0]["revenue"], 0.0)


class SeoDailyNormalizerNumberTests(SimpleTestCase):
    def test_a_float_shaped_conversion_count_does_not_raise(self):
        resp = _Response([
            # date, country, device, pagePath
            _Row(["20260605", "United States", "MOBILE", "/pricing"],
                 # sessions, screenPageViews, conversions, bounceRate, users, newUsers, engRate
                 ["10", "20", "2.0", "0.4", "9", "5", "0.6"]),
        ])
        records = GA4Connector._normalize(GA4Connector.__new__(GA4Connector), resp,
                                          "https://fusehealth.com/")
        self.assertEqual(records[0]["conversions"], 2)
        self.assertEqual(records[0]["landing_page"], "https://fusehealth.com/pricing")
