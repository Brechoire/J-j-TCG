"""Client minimal Wikimedia : timeouts, retry backoff, User-Agent, lots."""

import time

import requests

USER_AGENT = "JejeTCG/0.1 (contact:admin@example.com)"
TIMEOUT_S = 10
MAX_RETRIES = 3


class WikidataClient:
    DEFAULT_INSTANCE_OF = "Q5"
    DEFAULT_OCCUPATION_QID = "Q937857"

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

    def fetch_qids(
        self,
        limit: int,
        instance_of: str = DEFAULT_INSTANCE_OF,
        occupation_qid: str | None = DEFAULT_OCCUPATION_QID,
        sport_qid: str | None = None,
    ) -> list[str]:
        """Requête SPARQL générique paramétrée par `import_config` collection.

        Défauts = joueur de foot : P31=Q5 (humain) + P106=Q937857 (footballeur).
        `occupation_qid=None` → filtre P31 seul (ex. stades Q483110).
        `sport_qid` → filtre P641 (ex. stades de foot : Q2736).
        Ex. entraîneurs : instance_of=Q5, occupation_qid=Q628099.
        """
        import re

        if not re.fullmatch(r"Q\d+", instance_of or ""):
            raise ValueError(f"instance_of invalide : {instance_of!r}")
        if occupation_qid and not re.fullmatch(r"Q\d+", occupation_qid):
            raise ValueError(f"occupation_qid invalide : {occupation_qid!r}")
        if sport_qid and not re.fullmatch(r"Q\d+", sport_qid):
            raise ValueError(f"sport_qid invalide : {sport_qid!r}")
        # 1 seule requête SPARQL limitée (liste QID), détails via Action API par lots.
        # ORDER BY pour un périmètre stable entre runs (sinon LIMIT seul = tirage arbitraire).
        clauses = [f"?item wdt:P31 wd:{instance_of} ."]
        if occupation_qid:
            clauses.append(f"?item wdt:P106 wd:{occupation_qid} .")
        if sport_qid:
            clauses.append(f"?item wdt:P641 wd:{sport_qid} .")
        type_pattern = "\n          ".join(clauses)
        query = f"""
        SELECT ?item WHERE {{
          {type_pattern}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
        }} ORDER BY ?item LIMIT {int(limit)}
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

    def fetch_football_qids(self, limit: int) -> list[str]:
        # Compat historique : joueur de foot uniquement.
        return self.fetch_qids(limit)

    def fetch_pageviews_60d(self, fr_titles: list[str], days: int = 60) -> dict[str, int | None]:
        """Visites Wikipédia FR par article sur les `days` derniers jours (somme).

        API Wikimedia REST `per-article`. Titre sans article → None (jamais inventé).
        Une erreur sur un titre ne fait pas échouer les autres.
        """
        import datetime
        from urllib.parse import quote

        end = datetime.date.today() - datetime.timedelta(days=1)
        start = end - datetime.timedelta(days=int(days) - 1)
        start_s, end_s = start.strftime("%Y%m%d"), end.strftime("%Y%m%d")
        views: dict[str, int | None] = {}
        for title in dict.fromkeys(t for t in fr_titles if t):
            article = quote(title.replace(" ", "_"), safe="")
            url = (
                "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
                f"fr.wikipedia/all-access/user/{article}/daily/{start_s}/{end_s}"
            )
            try:
                data = self._get(url, {})
                items = data.get("items") or []
                total = sum(int(i.get("views", 0)) for i in items)
                views[title] = total if items else None
            except Exception:
                views[title] = None
        return views

    # Propriétés dont la valeur est une entité à résoudre en libellé FR.
    ENTITY_PROPS = ("P27", "P413", "P54", "P276", "P286")

    @staticmethod
    def _referenced_qids(claims: dict) -> set[str]:
        """QID d'entités référencées par les props (nationalité, poste, club)."""
        found: set[str] = set()
        for prop in WikidataClient.ENTITY_PROPS:
            for statement in claims.get(prop) or []:
                mainsnak = (statement.get("mainsnak") or {}).get("datavalue") or {}
                v = mainsnak.get("value")
                if isinstance(v, dict) and (v.get("id") or "").startswith("Q"):
                    found.add(v["id"])
        return found

    def fetch_labels(self, qids: list[str]) -> dict[str, str]:
        """Libellés FR (repli EN) pour des QID — 1 requête / 50, jamais d'exception."""
        labels: dict[str, str] = {}
        uniq = [q for q in dict.fromkeys(qids) if q]
        for i in range(0, len(uniq), 50):
            batch = uniq[i : i + 50]
            try:
                data = self._get(
                    "https://www.wikidata.org/w/api.php",
                    {
                        "action": "wbgetentities",
                        "ids": "|".join(batch),
                        "languages": "fr|en",
                        "props": "labels",
                        "format": "json",
                    },
                )
            except Exception:
                data = {}
            for qid in batch:
                ent = (data.get("entities") or {}).get(qid, {})
                lab = (ent.get("labels") or {})
                labels[qid] = (lab.get("fr") or {}).get("value", "") or (
                    lab.get("en") or {}
                ).get("value", "")
        return labels

    def fetch_entities(self, qids: list[str], with_pageviews: bool = True) -> list[dict]:
        out: list[dict] = []
        raw_by_qid: dict[str, dict] = {}
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
                raw_by_qid[qid] = ent
        # Résout nationalité/poste/club (QID → libellé FR) avant parsing.
        ref_qids: set[str] = set()
        for ent in raw_by_qid.values():
            ref_qids |= self._referenced_qids(ent.get("claims") or {})
        labels = self.fetch_labels(sorted(ref_qids))
        for qid in qids:
            out.append(self._parse_entity(qid, raw_by_qid.get(qid, {}), labels))
        if with_pageviews:
            titles = [
                ((d.get("sitelinks") or {}).get("frwiki") or {}).get("title", "")
                for d in (raw_by_qid.get(q, {}) for q in qids)
            ]
            views = self.fetch_pageviews_60d([t for t in titles if t])
            title_by_qid = dict(zip(qids, titles, strict=False))
            for parsed, qid in zip(out, qids, strict=False):
                parsed["pageviews_60d"] = views.get(title_by_qid.get(qid, ""), None)
        return out

    @staticmethod
    def _parse_entity(qid: str, ent: dict, resolved: dict | None = None) -> dict:
        import re
        from urllib.parse import quote

        resolved = resolved or {}
        ent_labels = ent.get("labels") or {}
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
                # Valeur entité (ex. club) : libellé FR résolu, repli QID.
                if (v.get("id") or "").startswith("Q"):
                    return resolved.get(v["id"]) or v["id"]
                return v.get("text") or v.get("id") or ""
            return str(v) if v else ""

        def claim_filename(prop):
            """P18 image : datavalue.value = nom de fichier Commons (str)."""
            vals = claims.get(prop) or []
            if not vals:
                return ""
            mainsnak = (vals[0].get("mainsnak") or {}).get("datavalue") or {}
            v = mainsnak.get("value")
            if isinstance(v, str) and v.strip():
                return v.strip()
            if isinstance(v, dict):
                # Garde-fou si format inattendu.
                text = v.get("text") or ""
                return text.strip()
            return ""

        def claim_quantity(prop):
            """P1083 capacité : datavalue {amount:"+81344",unit:"1"} → "81 344"."""
            vals = claims.get(prop) or []
            if not vals:
                return ""
            mainsnak = (vals[0].get("mainsnak") or {}).get("datavalue") or {}
            v = mainsnak.get("value")
            if not isinstance(v, dict):
                return ""
            try:
                return f"{int(float(v.get('amount', 0))):,}".replace(",", " ")
            except (TypeError, ValueError):
                return ""

        label_fr = (ent_labels.get("fr") or {}).get("value", "") or (
            ent_labels.get("en") or {}
        ).get("value", "")
        fr_title = (sitelinks.get("frwiki") or {}).get("title", "")
        # Nom façon Wikipédia : le titre d'article FR prime sur le libellé
        # Wikidata (ex. "Stade Buffalo" plutôt que "stade Buffalo"), sauf
        # titre homonymique "X (…)" qui n'est pas le nom courant.
        if fr_title and not re.search(r"\s\(.*\)\s*$", fr_title):
            label_fr = fr_title
        filename = claim_filename("P18")
        if filename:
            image_url = (
                "https://commons.wikimedia.org/wiki/Special:FilePath/"
                f"{quote(filename)}?width=500"
            )
            image_attribution = f"{filename} — Wikimedia Commons"
            image_license = "Licence Commons (voir page fichier)"
        else:
            image_url = ""
            image_attribution = ""
            image_license = ""
        return {
            "wikidata_id": qid,
            "label_fr": label_fr,
            "description_fr": (descs.get("fr") or {}).get("value", ""),
            "wikipedia_url_fr": f"https://fr.wikipedia.org/wiki/{fr_title.replace(' ', '_')}"
            if fr_title
            else "",
            "props": {
                "birth": claim_text("P569"),
                "nationality": claim_text("P27"),
                "position": claim_text("P413"),
                "club": claim_text("P54"),
                "capacity": claim_quantity("P1083"),
                "location": claim_text("P276"),
                "team": claim_text("P286"),
            },
            "image_url": image_url,
            "image_attribution": image_attribution,
            "license": image_license,
            "pageviews_60d": None,
        }
