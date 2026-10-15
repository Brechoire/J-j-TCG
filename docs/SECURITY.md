# Sécurité

- CSRF actif, `SESSION_COOKIE_HTTPONLY`, `CSRF_COOKIE_SECURE` + `SESSION_COOKIE_SECURE` en prod (HTTPS), `SECURE_HSTS`, `X-Frame-Options`, `Referrer-Policy`.
- Auth : custom User UUID, hash PBKDF2/Argon2, login throttled, sessions invalidées à la déconnexion.
- Autorisations : joueurs jamais create/update collection/carte/rareté (403 testé) ; admin `is_staff` uniquement, chaque vue admin vérifiée.
- Validation serveur systématique : prix/valeurs recalculés, jamais depuis POST. Idempotence : `idempotency_key` unique, double-submit bloqué.
- XSS : auto-escape, pas de `|safe` sur données wiki, URLs validées. Rate limiting : cooldown + throttle ouverture/achat/vente + login.
- Secrets : `.env` + variables d'env, jamais en Git (`.gitignore` : `.env`, `db.sqlite3`, `__pycache__`). Logs sans PII, audit `WalletTransaction`.
- RGPD : export/suppression compte, mentions attribution Wikimedia.
