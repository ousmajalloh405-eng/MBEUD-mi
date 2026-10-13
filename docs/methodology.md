# Méthodologie

1. **Découper** le territoire en cellules de 500 m (`config/settings.yaml`, `cell_size_m`).
2. **Associer** à chaque cellule des attributs (altitude, pente, historique, drainage, population, infrastructures, routes).
3. **Valider** les données (manquantes, doublons, coordonnées, plages, unités, timestamps).
4. **Normaliser** chaque variable entre 0 (favorable) et 1 (défavorable).
5. **Calculer** les trois blocs : Hazard, Vulnerability, Exposure.
6. **Combiner** en un score 0-100 et classer en 5 niveaux.
7. **Simuler** : le même calcul est rejoué pour n'importe quelle pluie (50 → 150 mm ou valeur libre).
8. **Recommander** : texte par niveau, formulé en « priorités proposées ».
9. **Proposer** une allocation de ressources (simulation algorithmique, pas un ordre).

## Hazard / Exposure / Vulnerability / Risk

| Notion | Question | Dans le projet |
|---|---|---|
| Hazard | Quelle intensité du phénomène ? | pluie 24 h |
| Exposure | Qu'est-ce qui se trouve là ? | population, infrastructures critiques, routes |
| Vulnerability | La zone encaisse-t-elle l'eau ? | basse altitude, pente faible, historique, drainage |
| Risk | Combinaison des trois | score 0-100 |

Exemple : un hôpital (exposition) dans une cuvette mal drainée (vulnérabilité) lors de 120 mm (aléa) → risque élevé.
Le même hôpital en hauteur, avec bon drainage → vulnérabilité faible → risque plus faible, même avec la même pluie.

## Étape ML (future)
Pas de ML dans le MVP : un modèle explicable d'abord. Si des données historiques fiables sont obtenues (EO4SD, UNOSAT, rapports), étudier classification / Random Forest / XGBoost pour estimer la probabilité qu'une zone soit fortement impactée, en gardant le score comme référence de comparaison.
