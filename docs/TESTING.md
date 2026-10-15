# Tests

- Stack : **pytest-django** (frais, pas unittest seul à terme), Playwright desktop + mobile, Ruff.
- TDD raisonnable : test d'abord pour services (`RarityAssignmentService`, `BoosterOpeningService`, `BoosterPurchaseService`, `CardSaleService`), permissions, idempotence, concurrence.
- Cas obligatoires : inscription/connexion, admin-only, import incrémental + timeout, correction verrouillée préservée, répartition catalogue, 5 distinctes/booster, cooldown global, 1er gratuit, double ouverture simultanée, achat OK/KO, achat sans toucher cooldown, vente doublons, refus dernier exemplaire, intégrité wallet, transactions concurrentes, idempotence, progression album.
- Stats : tirages sur N significatif avec marges (ex chi2 souple), + tests déterministes seedés pour règles exactes.
- E2E : inscription → booster → album → vente → achat, desktop 1280 + mobile 390, `prefers-reduced-motion` respecté.
- Commandes : `pytest -q`, `pytest -m "not e2e"`, `playwright test`.
