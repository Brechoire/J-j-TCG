# Import Wikidata / Wikipédia / Commons

Commande : `python manage.py import_wikidata football --limit 100 [--dry-run] [--qid Q42] [--resume]`

## 1. Périmètre Football MVP

100 à 500 footballeurs réels. Champs si dispo : nom, QID, description FR, naissance, nationalité, poste, club (marqué potentiellement obsolète + `fetched_at`), image Commons, article FR, pageviews, métadonnées rareté. Placeholder visuel si sans image. Ne jamais inventer.

## 2. Robustesse (exigée)

- **Max 100 requêtes** par run initial (validé). Lots WBSearch/Wikidata API + `wbgetentities`, pas de SPARQL massif.
- User-Agent identifiable (`WikiCardsMVP/0.1 contact:admin@example.com`), timeouts 10s, retry backoff exponentiel 3×, respect 429/Retry-After.
- Sauvegarde progression tous les 10 items (`ImportJob.progress`), reprise `--resume`, anti-doublons par `wikidata_id`, incrémental, `--dry-run`, réimport `--qid`, journal erreurs JSON.
- Zéro appel réseau pendant ouverture booster (données pré-importées).

## 3. Licences

Conserver `image_attribution`, `license`, URL article. Textes : CC BY-SA, images : licence Commons respective + auteur. Affichage fiche carte obligatoire.
