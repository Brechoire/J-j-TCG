# Système de rareté hybride

## 1. Quatre valeurs distinctes

1. `auto_score` : popularité encyclopédique mesurée (pas une valeur sportive).
2. `auto_rarity` : proposée par seuils configurables.
3. `rarity` : effectivement utilisée en jeu.
4. Correction manuelle + `is_locked`.

Sync Wikidata n'écrase jamais `rarity` si `is_locked=True`.

## 2. Score Football (données réellement dispo)

- Source : **pageviews Wikipédia FR 60 jours** (`pageviews_60d`) via API Wikimedia, + bonus complétude (image ? description ? club/poste renseignés ?).
- Formule v1 (configurable, documentée dans admin) : `score = log1p(pageviews_60d) + 0.5*has_image + 0.3*has_description + 0.2*has_club`.
- Repli : si `pageviews_60d` absent → score sur complétude seule + flag `low_signal=True`, rangé par défaut en Commune/Peu commune selon seuils. Ne jamais inventer.
- Mention UI : « Popularité encyclopédique », pas « valeur sportive ».

## 3. Seuils → distribution catalogue cible

Cible configurable : Commune 55 % / Peu commune 25 % / Rare 12 % / Épique 6 % / Légendaire 2 % **du catalogue** (≠ probas de tirage, même chiffres par coïncidence MVP).
Méthode : tri par `auto_score`, découpe par quantiles cibles, admins ajustent seuils en prévisualisation.

## 4. Admin

Liste : `auto_score`, `auto_rarity`, `rarity` éditable, `is_locked` toggle, actions `recalculer auto`, `prévisualiser distribution`. Historique des corrections.
