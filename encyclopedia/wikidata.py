"""Client minimal Wikimedia : timeouts, retry backoff, User-Agent, lots."""

import time

import requests

USER_AGENT = "WikiCardsMVP/0.1 (contact:admin@example.com)"
TIMEOUT_S = 10
MAX_RETRIES = 3


class WikidataClient:
    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def _get(self, url, params):
        last_exc = None
        for attempt in range(MAX_RETRIES):
            try:
                r = self.session.get(url, params=params, timeout=TIMEOUT_S)
                if r.status_code == 429:
                    last_exc = requests.HTTPError(f"429 Too Many Requests {url}")
                    time.sleep(2**attempt)
                    continue
                r.raise_for_status()
                return r.json()
            except (
                requests.Timeout,
                requests.HTTPError,
                requests.ConnectionError,
            ) as e:
                last_exc = e
                time.sleep(2**attempt)
        raise last_exc or requests.HTTPError(f"Échec requête {url}")

    def fetch_football_qids(self, limit: int) -> list[str]:
        # 1 seule requête SPARQL limitée (liste QID), détails via Action API par lots.
        query = f"""
        SELECT ?item WHERE {{
          ?item wdt:P31 wd:Q5 ;
                wdt:P106 wd:Q937857 .
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
        }} LIMIT {int(limit)}
        """
        data = self._get(
            "https://query.wikidata.org/sparql",
            {"query": query, "format": "json"},
        )
        qids = []
        for b in data.get("results", {}).get("bindings", []):
            uri = b.get("item", {}).get("value", "")
            qid = uri.rsplit("/", 1)[-1]
            if qid.startswith("Q"):
                qids.append(qid)
        return qids[: int(limit)]

    def fetch_entities(self, qids: list[str]) -> list[dict]:
        out: list[dict] = []
        for i in range(0, len(qids), 50):
            batch = qids[i : i + 50]
            data = self._get(
                "https://www.wikidata.org/w/api.php",
                {
                    "action": "wbgetentities",
                    "ids": "|".join(batch),
                    "languages": "fr|en",
                    "sitelinks": "frwiki",
                    "props": "labels|descriptions|sitelinks|claims",
                    "format": "json",
                },
            )
            for qid in batch:
                ent = (data.get("entities") or {}).get(qid, {})
                out.append(self._parse_entity(qid, ent))
        return out

    @staticmethod
    def _parse_entity(qid: str, ent: dict) -> dict:
        labels = ent.get("labels") or {}
        descs = ent.get("descriptions") or {}
        sitelinks = ent.get("sitelinks") or {}
        claims = ent.get("claims") or {}

        def claim_text(prop):
            vals = claims.get(prop) or []
            if not vals:
                return ""
            mainsnak = (vals[0].get("mainsnak") or {}).get("datavalue") or {}
            v = mainsnak.get("value")
            if isinstance(v, dict):
                return v.get("text") or v.get("id") or ""
            return str(v) if v else ""

        fr_title = (sitelinks.get("frwiki") or {}).get("title", "")
        return {
            "wikidata_id": qid,
            "label_fr": (labels.get("fr") or {}).get("value", "")
            or (labels.get("en") or {}).get("value", ""),
            "description_fr": (descs.get("fr") or {}).get("value", ""),
            "wikipedia_url_fr": f"https://fr.wikipedia.org/wiki/{fr_title.replace(' ', '_')}"
            if fr_title
            else "",
            "props": {
                "birth": claim_text("P569"),
                "nationality": claim_text("P27"),
                "position": claim_text("P413"),
                "club": claim_text("P54"),
            },
            "image_url": "",
            "image_attribution": "",
            "pageviews_60d": None,
        }
