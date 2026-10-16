from django.db import IntegrityError
from django.test import TestCase


class EncyclopediaEntityTests(TestCase):
    def test_wikidata_id_unique(self):
        from encyclopedia.models import EncyclopediaEntity

        EncyclopediaEntity.objects.create(wikidata_id="Q42", label="Douglas Adams")
        with self.assertRaises(IntegrityError):
            EncyclopediaEntity.objects.create(wikidata_id="Q42", label="Doublon")

    def test_minimal_fields(self):
        from encyclopedia.models import EncyclopediaEntity

        e = EncyclopediaEntity.objects.create(
            wikidata_id="Q1",
            label_fr="Test",
            pageviews_60d=123,
        )
        assert e.pk is not None


class PageviewsTests(TestCase):
    def _client_with(self, get_fn):
        from encyclopedia.wikidata import WikidataClient

        client = WikidataClient.__new__(WikidataClient)
        import requests

        client.session = requests.Session()
        client._get = get_fn
        return client

    def test_fetch_pageviews_sums_daily_views(self):
        client = self._client_with(
            lambda url, params: {"items": [{"views": 10}, {"views": 5}]}
        )
        views = client.fetch_pageviews_60d(["Lionel Messi"])
        assert views == {"Lionel Messi": 15}

    def test_fetch_pageviews_uses_fr_wikipedia_endpoint(self):
        seen = {}

        def fake_get(url, params):
            seen["url"] = url
            return {"items": [{"views": 1}]}

        client = self._client_with(fake_get)
        client.fetch_pageviews_60d(["Kylian Mbappé"])
        assert "fr.wikipedia" in seen["url"]
        assert "Kylian" in seen["url"]

    def test_fetch_pageviews_error_gives_none(self):
        import requests

        def boom(url, params):
            raise requests.HTTPError("404")

        client = self._client_with(boom)
        assert client.fetch_pageviews_60d(["Inconnu Xyz"]) == {"Inconnu Xyz": None}
        assert client.fetch_pageviews_60d([]) == {}


class EntityParseTests(TestCase):
    def _entity(self):
        return {
            "labels": {"fr": {"value": "Hugo Lloris"}},
            "descriptions": {"fr": {"value": "footballeur"}},
            "sitelinks": {},
            "claims": {
                "P54": [
                    {"mainsnak": {"datavalue": {"value": {"id": "Q12345"}}}},
                ],
                "P413": [
                    {"mainsnak": {"datavalue": {"value": {"id": "Q678"}}}},
                ],
            },
        }

    def test_parse_resolves_club_qid_to_french_label(self):
        from encyclopedia.wikidata import WikidataClient

        parsed = WikidataClient._parse_entity(
            "Q1", self._entity(), {"Q12345": "Tottenham Hotspur", "Q678": "gardien de but"}
        )
        assert parsed["label_fr"] == "Hugo Lloris"
        assert parsed["props"]["club"] == "Tottenham Hotspur"
        assert parsed["props"]["position"] == "gardien de but"

    def test_parse_falls_back_to_qid_without_label(self):
        from encyclopedia.wikidata import WikidataClient

        parsed = WikidataClient._parse_entity("Q1", self._entity(), {})
        assert parsed["props"]["club"] == "Q12345"

    def test_referenced_qids_collects_entity_props(self):
        from encyclopedia.wikidata import WikidataClient

        found = WikidataClient._referenced_qids(self._entity()["claims"])
        assert found == {"Q12345", "Q678"}

    def test_fetch_labels_prefers_french(self):
        from encyclopedia.wikidata import WikidataClient

        client = WikidataClient.__new__(WikidataClient)

        def fake_get(url, params):
            assert params["props"] == "labels"
            return {
                "entities": {
                    "Q12345": {"labels": {"fr": {"value": "Tottenham"}}},
                    "Q678": {"labels": {"en": {"value": "goalkeeper"}}},
                }
            }

        client._get = fake_get
        assert client.fetch_labels(["Q12345", "Q678"]) == {
            "Q12345": "Tottenham",
            "Q678": "goalkeeper",
        }


class CollectionTypeQueryTests(TestCase):
    def _client_with(self, get_fn):
        from encyclopedia.wikidata import WikidataClient

        client = WikidataClient.__new__(WikidataClient)
        import requests

        client.session = requests.Session()
        client._get = get_fn
        return client

    def test_fetch_qids_without_occupation_filters_p31_only(self):
        seen = {}

        def fake_get(url, params):
            seen["query"] = params["query"]
            return {"results": {"bindings": []}}

        client = self._client_with(fake_get)
        assert client.fetch_qids(10, instance_of="Q483110", occupation_qid=None) == []
        assert "wd:Q483110" in seen["query"]
        assert "P106" not in seen["query"]

    def test_fetch_qids_with_occupation_keeps_p106(self):
        seen = {}

        def fake_get(url, params):
            seen["query"] = params["query"]
            return {"results": {"bindings": []}}

        client = self._client_with(fake_get)
        client.fetch_qids(10, instance_of="Q5", occupation_qid="Q628099")
        assert "P106" in seen["query"] and "wd:Q628099" in seen["query"]

    def test_fetch_qids_with_sport_adds_p641(self):
        seen = {}

        def fake_get(url, params):
            seen["query"] = params["query"]
            return {"results": {"bindings": []}}

        client = self._client_with(fake_get)
        client.fetch_qids(
            10, instance_of="Q483110", occupation_qid=None, sport_qid="Q2736"
        )
        assert "P641" in seen["query"] and "wd:Q2736" in seen["query"]
        assert "P106" not in seen["query"]

    def test_fetch_qids_rejects_bad_sport_qid(self):
        client = self._client_with(lambda url, params: {})
        import pytest

        with pytest.raises(ValueError, match="sport_qid"):
            client.fetch_qids(10, instance_of="Q483110", sport_qid="ZZZ")

    def test_parse_formats_stadium_capacity(self):
        from encyclopedia.wikidata import WikidataClient

        ent = {
            "labels": {"fr": {"value": "Stade de France"}},
            "descriptions": {},
            "sitelinks": {},
            "claims": {
                "P1083": [
                    {"mainsnak": {"datavalue": {"value": {"amount": "+81344", "unit": "1"}}}}
                ],
                "P276": [{"mainsnak": {"datavalue": {"value": {"id": "Q123"}}}}],
            },
        }
        parsed = WikidataClient._parse_entity("Q1234", ent, {"Q123": "Saint-Denis"})
        assert parsed["props"]["capacity"] == "81 344"
        assert parsed["props"]["location"] == "Saint-Denis"

    def test_resolve_import_config_accepts_null_occupation(self):
        from encyclopedia.importer import resolve_import_config

        class Col:
            import_config = {"instance_of": "Q483110", "occupation_qid": None}

        assert resolve_import_config(Col()) == {
            "instance_of": "Q483110",
            "occupation_qid": None,
        }

    def test_parse_prefers_wikipedia_title_over_label(self):
        from encyclopedia.wikidata import WikidataClient

        ent = {
            "labels": {"fr": {"value": "stade Buffalo"}},
            "descriptions": {},
            "sitelinks": {"frwiki": {"title": "Stade Buffalo"}},
            "claims": {},
        }
        parsed = WikidataClient._parse_entity("Q1", ent, {})
        assert parsed["label_fr"] == "Stade Buffalo"

    def test_parse_rejects_disambiguated_title(self):
        from encyclopedia.wikidata import WikidataClient

        ent = {
            "labels": {"fr": {"value": "Michel"}},
            "descriptions": {},
            "sitelinks": {"frwiki": {"title": "Michel (football)"}},
            "claims": {},
        }
        parsed = WikidataClient._parse_entity("Q1", ent, {})
        assert parsed["label_fr"] == "Michel"
