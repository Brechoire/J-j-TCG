# Backlog WikiCards — MVP

## Phase 0 — Analyse [x]
- [x] Audit dépôt (Django 5.2.18, home accueil, SQLite)
- [x] PRD, ARCHITECTURE, DATABASE, GAME_RULES, ECONOMY, RARITY, IMPORT, SECURITY, TESTING, DEPLOYMENT
- [ ] Décisions restantes : `AUTH_USER_MODEL` UUID, seuils rareté Football, source pageviews exacte

## Phase 1 — Fondations [x]
- [x] pytest-django, Ruff, pre-commit, GitHub Actions
- [x] Tailwind local + base responsive + nav basse
- [x] `core` + `accounts` (User UUID, profil, auth, profil page)
- [x] Variables d'env, `.gitignore`, `check` vert (`check --deploy` : 6 warnings dev attendus, prod via env)

## Phase 2 — Collections/cartes [x]
- [x] `collection` (= `collections` spec, renommé : conflit stdlib Python), `encyclopedia`, `cards` + admin + `RarityAssignmentService`
- [x] Contraintes uniques, distribution catalogue 55/25/12/6/2 (testée à 100 cartes, verrou préservé)

## Phase 3 — Import Football [x]
- [x] `import_wikidata football --limit 100` (lots 50, backoff 3×, resume, dry-run, réimport QID, max 100/run)
- [x] Entités + cartes + pageviews/attributions + rareté auto (seed raretés si vide)
- [ ] 100 cartes réelles : à lancer (`--limit 100`, réseau requis, job traçable)
- [x] Correction/verrou admin déjà en place (Phase 2)

## Phase 4 — Boosters gratuits [x]
- [x] `BoosterOpeningService` : 5 distinctes, pondéré sans remplacement + redistribution, cooldown 600s global, idempotence clé, historique (relecture par clé)
- [x] `inventory` upsert quantité, `select_for_update` Postgres / même code SQLite (limite documentée)
- [x] Vues : `POST /boosters/ouvrir/<slug>/` → 302 résultat, `GET /boosters/<pk>/`, `GET /boosters/historique/`, 429 si cooldown

## Phase 5 — Album [x]
- [x] `inventory.services.get_album_data` : progression uniques, filtres rareté/recherche, missing/discovered/duplicates
- [x] Pages : `/collections/`, `/collections/<slug>/` (avec bouton ouvrir booster), `/albums/<slug>/`, `/albums/<slug>/<id>/`, `/inventaire/`

## Phase 6 — Économie [ ]
- [ ] `Wallet`, `CardSaleService` (5/15/50/150/500, min 1), `BoosterPurchaseService` (250, sans toucher cooldown), `simulate_economy`

## Phase 7 — Mobile [ ]
- [ ] Révélation cartes, effets rareté, reduced-motion, WCAG 2.2 AA, perf

## Phase 8 — Stabilisation [ ]
- [ ] E2E Playwright, audit sécu, docs à jour, déploiement
