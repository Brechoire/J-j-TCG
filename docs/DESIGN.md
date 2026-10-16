# WikiCards — Design system & maquettes

> Statut : appliqué (refonte TCG sombre, octobre 2026). Maquettes statiques : `design/` (voir `design/index.html`).
> Source de vérité des tokens et composants : `static/src/input.css` (`@theme` + `@layer components`).
> Ce document décrit l'intention, les règles d'usage et la transposition vers les templates Django.

## 1. Principes directeurs

1. **Une seule ambiance : TCG sombre premium.** Tout le site est sombre et immersif (référence Magic Arena) : fond profond + halo radial, cartes « posées » comme des objets de collection, raretés métalliques. Fini la double ambiance Encyclo/Boost : les tokens `boost-*` sont fusionnés dans le défaut.
2. **L'encyclopédie d'abord.** Le contenu (noms, photos, attributions, chiffres) est roi ; la décoration ne porte jamais une information seule.
3. **Dopamine maîtrisée.** L'écran de révélation procure l'excitation du tirage, sans dark pattern : animations courtes, dans le contrôle de l'utilisateur (tap, « Tout révealer »), aucune fausse rareté, aucun compte à rebours culpabilisant.
4. **Mobile-first réel.** 375 px sans scroll horizontal, cibles ≥ 44 px, nav basse avec safe-area, densité adaptée (2 col. album → 4 col. desktop).
5. **Accessible par construction.** Contrastes mesurés (voir §8), focus visible, `prefers-reduced-motion` respecté, fonctionnement sans JavaScript (révélation = repli statique complet).

## 2. Ambiance

| Ambiance | Fond | Pages | Règles |
|---|---|---|---|
| **TCG** (sombre) | `canvas` #070B14 + halo radial | toutes : accueil, collections, album, fiche carte, historique, doublons, vente, boutique, profil, auth, ouverture, minuteur, révélation | Panels bleu nuit, bordures `line-strong`, accent bleu clair pour actions et liens, cartes parchemin « posées » sur le fond sombre ; flux booster immersif : pas de nav basse, sortie explicite en haut à gauche |

## 3. Fondations (tokens)

Tous les tokens vivent dans `static/src/input.css` :

```css
@theme {
  --color-canvas: #070b14; --color-surface: #0f172a;
  --color-line: #1e293b;          /* séparateurs décoratifs uniquement */
  --color-line-strong: #5a7091;   /* bordures interactives, ≥ 3:1 sur surface */
  --color-ink: #f1f5f9; --color-ink-muted: #94a3b8; --color-ink-subtle: #7d8fa8;
  --color-accent: #93c5fd; --color-accent-strong: #bfdbfe; --color-accent-tint: #16294d;
  --color-coin: #fbbf24; --color-coin-bright: #f59e0b; --color-coin-tint: #231a05;
  --color-success: #4ade80; --color-success-tint: #0b2e16;
  --color-danger: #f87171; --color-danger-tint: #2f1212;
  /* Raretés (inchangées) : accent / texte clair / texte sombre / fond teinté */
  --color-common: #64748b;    --color-common-ink: #334155;    --color-common-ink-dark: #cbd5e1;    --color-common-tint: #f1f5f9;
  --color-uncommon: #16a34a;  --color-uncommon-ink: #15803d;  --color-uncommon-ink-dark: #4ade80;  --color-uncommon-tint: #f0fdf4;
  --color-rare: #2563eb;      --color-rare-ink: #1d4ed8;      --color-rare-ink-dark: #60a5fa;      --color-rare-tint: #eff6ff;
  --color-epic: #9333ea;      --color-epic-ink: #7e22ce;      --color-epic-ink-dark: #c084fc;      --color-epic-tint: #faf5ff;
  --color-legendary: #f59e0b; --color-legendary-ink: #b45309; --color-legendary-ink-dark: #fbbf24; --color-legendary-tint: #fffbeb;
}
```

**Rôles de couleur** : `canvas`/`surface`/`line` = structure ; `ink` 3 niveaux = texte ; `accent` = actions et liens (bleu clair sur sombre) ; `coin` = crédits ; `success`/`danger` = états ; chaque rareté expose 4 variantes (accent décor, texte sur tint clair, texte sur sombre, tint de badge).
Les tokens `boost-*` historiques sont conservés en alias (mêmes valeurs) pour compatibilité des maquettes et du halo radial.

**Typographie** : pile système uniquement (`ui-sans-serif, system-ui…`) — aucune police externe au MVP. Titres 700–800 avec `tracking-tight`, labels de section `text-xs` capitales `tracking-widest`, chiffres en `tabular-nums`. Échelle Tailwind standard (12 → 30 px).

**Espacements / rayons / ombres** : échelle 4 px Tailwind ; rayons max `rounded-xl` (12 px, `0.75rem`), pack 16 px ; ombres limitées au duo `shadow-xl` (pack) et `shadow-lg` (barre de sélection flottante) ; les panels utilisent une bordure, pas une ombre.

**Motion** : interactions 150 ms, transitions de vues 300–400 ms, sheen holo 6 s (boucle douce), pulsation légendaire 1,4 s (une fois). Tout est encapsulé dans `@media (prefers-reduced-motion: no-preference)` : en mouvement réduit, les états changent **instantanément** — la fonctionnalité n'est jamais retirée.

## 4. Composants (classes `@layer components`)

### 4.1 Boutons — `.btn`
- Variantes : `.btn--primary` (bleu clair, texte encre sombre), `.btn--secondary` (surface bleutée, bordure `line-strong`), `.btn--ghost` (texte accent, fond tinté au hover), tailles `.btn--lg`, plein largeur `.btn--block`.
- États : `hover`, `focus-visible` (outline accent 2 px offset 2), `active` (translation 1 px), `disabled` (`opacity .5`, `cursor: not-allowed`), chargement à traiter côté app (bouton désactivé + libellé).
- Cible tactile : hauteur min 44 px (`.btn` = 2.75 rem, `.btn--lg` = 3.25 rem).

### 4.2 Carte TCG — `.pk-card` (composant central, implémenté en Django)
- **Anatomie originale inspirée TCG** (aucun asset/nom Pokémon) : cadre **métallique** couleur rareté (acier → or légendaire, halo lumineux rare/épique/légendaire) → en-tête (pastille type `FOOTBALLEUR`/`ENTRAÎNEUR`/`STADE`, nom, `POP` = score encyclopédique) → illustration portrait bordée (photo Commons ou initiale teintée rareté, badge rareté + drapeau `Nouvelle`/`Doublon ×N`/`×N`/`À découvrir`, bandeau pays + drapeau et N° — ex. « 🇫🇷 France · PSG », jamais de QID) → pied (valeur, quantité ou « Non possédée », N° catalogue) → attribution minuscule.
- La carte reste un **objet clair** (parchemin, encre sombre figée) posé sur la table sombre : lisibilité garantie quel que soit le thème.
- **Nationalités** (`cards/country_flags.py` + filtres `country_display`/`flag_img_url`/`is_qid`) : libellé FR → drapeau FlagCDN (`w40`, `onerror` silencieux) ; QID ou vide → repli club/Football, jamais de fuite « Q123 ». Note Windows : ne concerne plus que l'emoji de repli (non utilisé).
- **Partial unique** : `cards/templates/cards/_pk_card.html` (contexte : `card`, `quantity`, `discovered`, `size`, `badge`, `number`, `total`). Le parent choisit `<a>` (possédée) ou `<div>` (à découvrir) ; holo automatique pour rare/épique/légendaire possédées ; `aria-label` sur les silhouettes.
- **États** : possédée (complète + lien fiche) · `pk-card--missing` (nom `???`, art `?` hachurée, pas de holo) · `pk-card--holo` (reflet rainbow + glare suivant le pointeur, tilt 3D ≤ 16°, pointeur fin uniquement) · `pk-card--xs` (grilles : attribution masquée).
- **Ratio** : 63:88 (standard carte à jouer), `aspect-ratio` — la carte s'adapte à sa grille sans fixer de hauteur.
- `prefers-reduced-motion` : tilt et glare désactivés, holo statique atténué — la carte reste entièrement lisible.

### 4.3 Badge et pastille de rareté — `.rarity-badge`, `.rarity-dot`
- Pastille + libellé FR, fond tint de rareté, bordure 35 % de l'accent. `.rarity-dot` seul = version compacte (mini cartes). Les libellés rareté ne sont jamais remplacés par la couleur seule.

### 4.4 Chips de filtre — `.chip`, `.chip--active`
- Filtres album : lignes scrollables **contenues** (`overflow-x-auto`, pas de débordement de page). Actif = fond bleu profond, texte blanc. Utilisées aussi comme composition `aria-pressed` pour les groupes de filtres.

### 4.5 Formulaires — `.field`
- Label au-dessus, aide (`field__help`), état erreur (`.field--error` : bordure danger + `.field__error` avec icône et texte, `aria-invalid` + `aria-describedby`). Bordures de champ ≥ 3:1 (`line-strong`).
- Auth : pages étroites (`max-w-sm`), titre + phrase rassurante, erreurs par champ + résumé `alert--error`.

### 4.6 Messages — `.alert--error|success|info`
Résumé de formulaire, confirmations d'économie, note « anti double-débit » de la boutique. `role="alert"` pour les erreurs bloquantes, `role="note"` pour l'information.

### 4.7 Progression, stats, états vides
- `.progress` + `.progress__bar` : complétion d'album, minuteur, raretés (barres teintées via `bg-common…`).
- `.stat` : valeur 800 `text-2xl` tabulaire + libellé muted (accueil, collection, profil, inventaire).
- `.empty-state` : pointillés, message honnête + action principale (aucun doublon, thèmes à venir, album vide).

### 4.8 Portefeuille — `.wallet-chip`
Solde de crédits dans l'en-tête (icône pièce + montant abrégé). Le solde complet vit dans la boutique et le profil.

### 4.9 Navigation
- **`.top-bar`** : sticky, surface, bordure basse — logo, wallet chip, nav desktop (Collections · Tirages · Boutique · Profil).
- **`.bottom-nav`** : mobile uniquement, 5 onglets — **Accueil · Collections · Booster · Doublons · Profil** ; onglet Booster en `--action` (accent), état actif `aria-current="page"`, `env(safe-area-inset-bottom)`.
  - Changement assumé vs l'existant : « Tirages » quitte la nav basse (accessible depuis l'accueil et le profil) au profit de « Doublons », cœur de la boucle économique.
  - Écrans du flux booster : pas de nav basse (immersion), sortie explicite.
- **Aucune section active** sur les pages utilitaires (vente, boutique) : les onglets restent en couleur par défaut.

## 5. Écran signature — révélation de booster

**Storyboard** (`design/booster-revelation.html`, `boosters/result.html`) :
0. Arrivée : le sachet (`static/img/pack-football-legends.jpg`) avec bouton « Ouvrir le pack » — au clic, secousse + flash + déchirure (~1,5 s, `static/js/pack-open.js`), puis la séquence démarre. Sans JS : pas d'intro, cartes visibles d'emblée. `prefers-reduced-motion` : bascule instantanée.
1. Arrivée : une carte face cachée centrée — son dos affiche le visuel pack fourni (`static/img/pack-football-legends.jpg`, optimisé depuis `media/`, section « Dos de carte » de `input.css`), fixe jusqu'au clic (aucun teaser par-dessus), **et un halo lumineux couleur rareté** (anneau flouté + ombres, pulsation douce ; choix assumé : la couleur annonce la rareté avant le flip) — compteur « Carte 1 sur 5 », bouton « Révéler la première carte », échappatoire « Tout révéler », sortie explicite.
2. Tap sur le dos ou le bouton → la face se révèle **et reste affichée en grand au milieu** (bande « Déjà révélées » en miniatures en dessous) ; annonce vocale « Carte N sur 5 : Nom, Rareté » ; le bouton devient « Passer à la carte suivante ».
3. Tap suivant → dos de la carte N+1 (compteur incrémenté). Dernière carte : le bouton devient « Voir le récapitulatif ».
4. Légendaire : pulsation dorée unique (1,4 s) à la révélation — pas de confetti, pas de son.
5. Fin : grille récap 5 cartes, raretés groupées, nouvelle(s) découverte(s), doublons et leur valeur, actions « Voir l'album », « Revendre les doublons », « Rejouer » (désactivé + minuteur) et lien d'achat.

**Technique** (implémenté : `boosters/result.html` + `static/js/reveal.js`) :
- Progressive enhancement strict : sans JavaScript, **toutes les cartes sont visibles** en liste (repli complet + liens d'action dans une note). Le séquencement n'existe que si `<html class="js">`.
- La vue annote chaque carte (`quantity`, `is_new` : quantité 1 = nouvelle) et fournit `rarity_summary` groupé pour le récapitulatif.
- `prefers-reduced-motion: reduce` : séquence conservée mais transitions supprimées (changements instantanés) ; le stagger de « Tout révéler » est désactivé.
- ARIA : `role="status" aria-live="polite"` sur les annonces ; dos de carte `aria-hidden` ; le contenu des faces reste lisible dans l'arbre d'accessibilité.
- Aucune dépendance JS : `reveal.js` + `pk-card.js` vanilla avec `defer`, aucun état côté client (le tirage serveur est conservé ; la relecture d'un historique rejoue la séquence, le résultat restant identique).

## 6. Pages et parcours

| Page | Ambiance | Maquette | Points clés |
|---|---|---|---|
| Accueil | Sombre | `accueil.html` | Booster gratuit en action principale, progression, derniers tirages, « comment ça marche » |
| Collections | Sombre | `collections.html` | Football + thèmes à venir (créés par l'équipe) |
| Collection Football | Sombre | `collection-football.html` | Répartition du catalogue par rareté, progression perso, note « popularité encyclopédique » |
| Album | Sombre | `album.html` (maquette) / `inventory/album.html` (réel) | Onglets Collection / Mes cartes / À découvrir / Doublons avec compteurs, recherche + rareté, grille `pk-card` (possédées liées, silhouettes `???`) |
| Fiche carte | Sombre | `carte.html` (maquette) / `inventory/card_detail.html` (réel) | Grande `pk-card` + faits, score encyclopédique, revente (bloquée si 1 seul exemplaire), attributions Commons/Wikidata ; non-possédée masquée avec appel au booster |
| Collection (catalogue) | Sombre | `collection/detail.html` (réel) | Catalogue complet : possédées liées avec quantité, à découvrir en silhouette, progression si connecté |
| Historique | Sombre | `booster-historique.html` | `<details>` natifs pour revoir les 5 cartes, pagination |
| Doublons | Sombre | `inventaire.html` | Quantités vendables, valeurs, sélection multiple + barre sticky, variante vide |
| Vente | Sombre | `vente.html` | Stepper borné (max = possédé − 1), montant serveur, confirmation + état succès |
| Boutique | Sombre | `boutique.html` | Solde, booster 250 crédits, « achat ≠ minuteur », état solde insuffisant |
| Profil | Sombre | `profil.html` | Stats, progression par rareté, activité récente, compte |
| Connexion / Inscription | Sombre | `auth-*.html` | États d'erreur accessibles par champ |
| Ouverture | Sombre | `booster-ouverture.html` | Pack, état prêt et état minuteur, « à savoir » |
| Révélation | Sombre | `booster-revelation.html` (maquette) / `boosters/result.html` (réel) | Écran signature (§5) : séquence une à une, badges Nouvelle/Doublon, récap groupé par rareté |

Données de maquette (factices, cohérentes entre pages) : 42/100 découvertes (26 C / 10 PC / 5 R / 1 E / 0 L), 37 doublons, solde 1 240, minuteur 09:41.

## 7. Navigation et flux

- Nav basse mobile 5 onglets (§4.9) ; desktop : liens en en-tête.
- Le flux booster (ouverture → révélation) s'affranchit de la nav basse : sortie « Quitter »/« Accueil » explicite en haut, actions de fin de séquence vers album/doublons/boutique.
- Décision de transposition : l'écran d'ouverture dédié suppose une route GET de confirmation avant le POST `boosters:open` (actuellement le POST part directement de l'accueil/collection). À trancher en transposition ; la maquette fonctionne dans les deux cas (l'accueil garde un CTA direct).

## 8. Accessibilité (WCAG 2.2 AA) — contrastes mesurés

Mesures (script, ratio calculé WCAG) — thème sombre, octobre 2026 :

| Paire | Ratio | Seuil |
|---|---|---|
| ink / canvas · ink / surface | 17.97 · 16.30 | 4.5 |
| ink-muted / surface · ink-subtle / canvas | 6.96 · 5.97 | 4.5 |
| accent (liens) / surface · texte encre sur btn primaire clair | 9.90 · 9.90 | 4.5 |
| coin / surface · coin / coin-tint | 10.69 · 10.30 | 4.5 |
| success / success-tint · danger / danger-tint | 8.51 · 6.24 | 4.5 |
| chip actif (blanc / bleu profond) | 6.70 | 4.5 |
| raretés : ink / tint (commune → légendaire) | 9.45 · 4.79 · 6.16 · 6.51 · 4.84 | 4.5 |
| raretés : ink-dark / surface | 12.02 · 10.25 · 7.02 · 6.76 · 10.69 | 4.5 |
| line-strong / surface · / canvas (bordures UI) | 3.54 · 3.90 | 3 |
| focus accent / surface | 9.90 | 3 |

**Exceptions documentées** (jamais porteuses d'information seules) :
- `--color-line` (~1.2:1) : séparateurs décoratifs et fonds de piste de progression ; les composants interactifs utilisent `line-strong`.
- Accents raretés sur blanc pour légendaire (2.15:1) et pièce ambre (2.15:1) : éléments décoratifs doublés d'un libellé texte (badge, montant).
- Halos, sheen, cadres métalliques et rubans dégradés : décoratifs, l'information rareté est toujours textuelle.

**Autres garanties** : focus visible global (`:focus-visible`, outline 2 px offset 2, couleur adaptée au fond sombre) ; cibles 44 px pour boutons/steppers, 36 px min pour les chips (≥ 24 px exigés) ; pas de scroll horizontal (vérifié sur les 15 maquettes à 375 px) ; `env(safe-area-inset-bottom)` sur la nav ; chiffres `tabular-nums` ; annonces `aria-live` de révélation.

## 9. Transposition vers Django (Phase 7 — réalisée, refonte sombre octobre 2026)

1. `home/templates/base.html` : `.top-bar` + `.bottom-nav` (5 onglets), skip-link, `aria-current` par vue, pastille `js`, blocs `extra_head`/`extra_js`, `pk-card.js` global avec `defer`.
2. Partial `cards/_pk_card.html` (variantes possédée/manquante/holo/xs, badges Nouvelle/Doublon/À découvrir, drapeau pays en légende, monogramme teinté sans photo) — utilisé par album, catalogue, fiche, résultat booster et mes cartes.
3. `boosters/result.html` : maquette `booster-revelation.html` transposée ; JS factorisé dans `static/js/reveal.js` (+ `static/js/pk-card.js` pour le tilt) chargés avec `defer` ; récapitulatif en grille avec `min-width:0` anti-chevauchement.
4. Les classes composants (`btn`, `pk-card`, etc.) sont compilées dans `output.css` (gitignoré, `npm run build:css` requis) — aucune configuration supplémentaire.
5. Attributions Commons : conserver la ligne de crédit sur la fiche et l'exiger avant toute image réelle (voir `docs/SECURITY.md`).
6. États serveur → UI : 429 cooldown → écran minuteur ; solde insuffisant → variante boutique ; min 1 exemplaire → revente désactivée ; idempotence → anti double-clic déjà couvert par le bouton désactivé + serveur.
7. Fait : `collection/list.html`, `boosters/history.html`, tri + filtre rareté `inventory/list.html`, pastilles rareté inventaire. Reste (Phase 6) : boutique/vente.

## 10. Vérifications effectuées (octobre 2026)

- Refonte TCG sombre : tokens remappés, `.theme-boost` supprimé (fusionné dans le défaut), cadres `pk-card` métalliques, carte-objet claire préservée (encre sombre figée).
- Build Tailwind v4 (`@tailwindcss/cli`) : `npm run build:css` OK ; tokens/composants générés (`pk-card`, holo/glare, reveal).
- Captures headless 1600 px + 375 px (accueil, collections, album, inventaire, historique, révélation, maquettes accueil/révélation/album) : pas de scroll horizontal, pas de chevauchement, cartes lisibles.
- Templates réels vérifiés sur données de dev (200 cartes) : album/collection/résultat sans débordement à 375 px, séquence de révélation et récapitulatif fonctionnels, repli sans JS conservé.
- Révélation testée en versions JS, sans JS, et `prefers-reduced-motion: reduce` (séquence conservée sans transition).
- Contrastes : re-mesurés sur le thème sombre, 19 paires ≥ seuils (texte 4.5:1, non-texte 3:1) ; exceptions décoratives documentées (§8).
- Suite Django (pytest) : 86 tests ; `ruff check` + `format` verts.

## 11. Hors périmètre

- Pas de police externe, pas de PWA, pas d'images réelles dans les maquettes.
- Les animations avancées (particules) sont volontairement exclues (perf mobile, motion).
- Boutique/vente : Phase 6.
