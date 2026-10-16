# Import Wikidata / Wikipédia / Commons

Commande : `python manage.py import_wikidata football --limit 100 [--dry-run] [--qid Q42] [--resume]`

## 1. Périmètres (config par collection via `import_config`)

- **Football** : `{"instance_of": "Q5", "occupation_qid": "Q937857"}`.
- **Entraîneurs** : `{"instance_of": "Q5", "occupation_qid": "Q628099"}` (mêmes props que joueurs).
- **Stades de foot** : `{"instance_of": "Q483110", "occupation_qid": null, "sport_qid": "Q2736"}` (requête P31+P641 ; props `capacity` P1083, `location` P276, `team` P286). Seuls les stades marqués football (P641=Q2736) entrent ; les fiches existantes sans marquage sont conservées (dont cartes possédées).

100 à 500 footballeurs réels. Champs si dispo : nom, QID, description FR, naissance, nationalité, poste, club (marqué potentiellement obsolète + `fetched_at`), image Commons, article FR, pageviews Wikipédia FR 60 j (API Wikimedia, somme ; `None` si pas d'article FR — sert au tri de rareté), métadonnées rareté. Placeholder visuel si sans image. Ne jamais inventer.

## 2. Robustesse (exigée)

- **Max 100 requêtes** par run initial (validé). Lots WBSearch/Wikidata API + `wbgetentities`, pas de SPARQL massif.
- User-Agent identifiable (`JejeTCG/0.1 contact:admin@example.com`), timeouts 10s, retry backoff exponentiel 3×, respect 429/Retry-After.
- Sauvegarde progression tous les 10 items (`ImportJob.progress`), reprise `--resume`, anti-doublons par `wikidata_id`, incrémental, `--dry-run`, réimport `--qid`, journal erreurs JSON.
- Zéro appel réseau pendant ouverture booster (données pré-importées).

## 3. Licences

Conserver `image_attribution`, `license`, URL article. Textes : CC BY-SA, images : licence Commons respective + auteur. Affichage fiche carte obligatoire.
