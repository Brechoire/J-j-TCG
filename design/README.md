# Maquettes du design — WikiCards

Pages HTML statiques de référence (données factices) pour le design de WikiCards.
Spécifications complètes : `docs/DESIGN.md`.

## Prévisualiser

```bash
npm run build:css        # compile static/css/output.css (Tailwind v4)
```

Puis ouvrez `design/index.html` dans un navigateur (double-clic suffit — les
chemins relatifs fonctionnent en `file://`). Alternative locale :

```bash
python -m http.server 8010
# → http://localhost:8010/design/
```

Après modification du CSS (`static/src/input.css`) ou des pages, relancez
`npm run build:css` et rechargez.

## Contenu

- `index.html` — galerie de toutes les maquettes
- Pages « TCG sombre » : accueil, collections, collection-football, album,
  carte, profil, booster-historique, inventaire, vente, boutique, auth-*
- Pages sombres « Boost » : booster-ouverture, booster-revelation (écran signature)

## Statut

- Maquettes statiques : aucune logique serveur, aucune donnée réelle.
- `booster-revelation.html` embarque un petit script vanilla de démonstration
  (séquence au tap, repli sans JS, respect de `prefers-reduced-motion`).
- Ces fichiers ne sont pas servis par l'application ; la transposition vers les
  templates Django est décrite dans `docs/DESIGN.md` §9.
