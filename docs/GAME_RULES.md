# Règles du jeu

- Booster : 5 cartes **distinctes** dans un booster, doublons OK entre boosters.
- Gratuit : 1er immédiat, puis toutes les **10 min**, **global** toutes collections. Choix collection avant ouverture. Tirage serveur, atomique, idempotent (clé UUID, double-clic safe, résultat conservé).
- Acheté : **250 crédits**, mêmes probas, ne touche pas au cooldown gratuit. MVP : achat = ouverture immédiate (abstraction stock prévue).
- Probas par emplacement : Commune 55 / Peu commune 25 / Rare 12 / Épique 6 / Légendaire 2. Tirage pondéré **sans remplacement** dans le booster. Si rareté sans éligible restant : redistribue son poids au prorata des raretés restantes (documenté + testé). Pas de garantie promise.
- Album : uniques découvertes / total, % complétion, filtres rareté, recherche, manquantes, quantités, fiches encyclopédiques avec attribution.
- Vente : 1 par 1 ou en lot, confirmation, garde min 1 exemplaire, montants serveur uniquement, historique comptable.
- Boutique : solde vérifié serveur, débit + attribution atomiques, anti double-débit.
