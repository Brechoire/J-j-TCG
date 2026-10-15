# Économie

- Prix booster : **250**. Vente doublons : Commune 5 / Peu commune 15 / Rare 50 / Épique 150 / Légendaire 500 (modifiable admin, historisée).
- Portefeuille : `Wallet.balance >= 0`, chaque mouvement → `WalletTransaction` avec `reference` unique et `balance_after` (audit).
- Vente : `quantity > 1` exigé, `transaction.atomic`, `select_for_update` sur entry + wallet, montants recalculés serveur depuis `Rarity.sale_value` (jamais depuis navigateur).
- Achat : vérif solde serveur, débit `F(balance - price)`, anti-rejeu par `idempotency_key`.
- Simulation : `python manage.py simulate_economy --players 1000 --days 30` (paramètres en CLI, pas en dur). Sorties : uniques moyens, doublons moyens, crédits gagnés/dépensés, boosters achetés, complétion, répartition obtenue. Objectif : progression sans frustration, sans achat réel, sans dark pattern.
