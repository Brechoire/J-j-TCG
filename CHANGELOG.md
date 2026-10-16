# Changelog

## [Non publié]
### Added
- Carte TCG originale inspirée TCG (`cards/_pk_card.html`) : en-tête FOOT/nom/POP, illustration portrait bordée, légende pays + drapeau (jamais de QID), pied stats, holo + tilt pointeur fin (désactivés en `reduced-motion`), silhouettes `???` pour les non-possédées.
- Album à onglets : Collection / Mes cartes / À découvrir / Doublons avec compteurs (`get_album_data` enrichi, alias `box=owned`) ; catalogue `collection/detail` complet avec état possédé/à découvrir ; fiche carte et mes cartes au même design.
- Révélation booster une à une en production (`boosters/result.html` + `static/js/reveal.js`) : dos avec teaser photo floutée + halo lumineux couleur rareté (CSS seul, sans turbulence SVG pour la perf mobile), carte révélée maintenue en grand au milieu (2 temps : révéler → suivante), bande « Déjà révélées », badges Nouvelle/Doublon (`is_new`, `quantity`), récapitulatif groupé par rareté, repli sans JS, annonces `aria-live`.
- Design system — `docs/DESIGN.md` : tokens Tailwind v4 (ambiances « Encyclo » clair / « Boost » sombre, 5 raretés), composants (carte TCG, badges, boutons, chips, nav basse 5 onglets, écran de révélation), contrastes WCAG AA mesurés.
- Maquettes statiques `design/` : 14 pages + galerie (parcours complet, économie, auth, écran signature de révélation avec repli sans JS et `prefers-reduced-motion`).
### Changed
- Tailwind v3 → **v4.3.3** : `static/src/input.css` migré (`@import "tailwindcss"`, `@theme`, `@source`), `tailwind.config.js` retiré, `@tailwindcss/cli` ajouté.

## [0.1.0] - 2026-10-15
### Added
- App `home` : `GET /` → 200, `base.html` + `home/index.html`, 4 tests.
- Docs Phase 0 FR : PRD, ARCHITECTURE, DATABASE, GAME_RULES, ECONOMY, RARITY_SYSTEM, WIKIDATA_IMPORT, SECURITY, TESTING, DEPLOYMENT, README, PROJECT_TASKS.
### Changed
- Django 6.1.2 → **5.2.18 LTS** (env), `MAILERS` → `EMAIL_BACKEND`, `requirements.txt` figé.
