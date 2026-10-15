# WikiCards — PRD (MVP)

> Statut : Phase 0 validée. Docs en français. Nom provisoire, identité originale (pas de reprise WikiMasters).

## 1. Vision

Jeu web responsive de collection encyclopédique. Principe : ouvrir des boosters de 5 cartes, compléter des albums thématiques, revendre les doublons contre des crédits virtuels pour racheter des boosters. Mobile-first, évolutif PWA. Aucun argent réel.

## 2. Décisions produit (définitives MVP)

1. Première collection : **Football**.
2. Collections créées/configurées uniquement par admins.
3. Cartes importées depuis Wikidata / Wikipédia / Wikimedia Commons.
4. Rareté calculée auto puis corrigeable manuellement (verrouillable).
5. Booster gratuit toutes les **10 minutes**.
6. Délai gratuit **global** à toutes les collections.
7. Booster = exactement **5 cartes distinctes**.
8. Doublons autorisés **entre** boosters.
9. Vente des doublons contre crédits virtuels.
10. Crédits → achat de boosters supplémentaires.
11. Aucun achat argent réel.
12. UI responsive, priorité smartphone.
13. Admin via Django Admin.
14. Code modulaire, extensible à d'autres thèmes.

## 3. Personas

- **Joueur mobile** : ouvre un booster gratuit, consulte album, vend doublons.
- **Collectionneur** : vise 100 % album Football, suit stats par rareté.
- **Admin** : crée collection, lance import, ajuste/verrouille raretés, suit stats.

## 4. Parcours MVP

Inscription → 1er booster gratuit immédiat → résultat 5 cartes → album/progression → attente 10 min ou achat 250 crédits → vente doublons → complétion.

Pages : accueil (`home`, existante), inscription, connexion, dashboard, collections, détail Football, ouverture, résultat, album, fiche carte, inventaire, vente, boutique, profil.

## 5. Hors scope MVP

- Argent réel, échanges entre joueurs, éditions parallèles, PWA installable complète, Redis/Celery/React, temps réel.
- Stock de boosters non ouverts : prévoir abstraction, mais achat = ouverture immédiate.

## 6. Contraintes

- Python 3.12+, Django **5.2 LTS** (env actuel : 5.2.18), Templates + HTMX + JS vanilla, Tailwind compilé local, SQLite dev / PostgreSQL prod, pytest-django, Playwright, Ruff + pre-commit, GitHub Actions.
- Windows + Linux Mint, Docker Compose optionnel.
- WCAG 2.2 AA / RGAA applicable, `prefers-reduced-motion`, pas de scroll horizontal mobile, nav basse sur smartphone.

## 7. Définition de terminé

Code fonctionne, tests passent, permissions OK, erreurs gérées, utilisable smartphone, migrations valides, docs à jour, aucun critique connu.
