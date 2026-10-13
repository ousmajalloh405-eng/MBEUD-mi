# Modèle de risque — Flood Risk Score

> Tous les coefficients, seuils et références ci-dessous sont des **hypothèses de départ non calibrées**. Ils sont dans `config/risk.yaml` et se modifient sans toucher au code.

## Variables et normalisation (0 = favorable, 1 = défavorable)

| Bloc | Variable | Normalisation | Pourquoi |
|---|---|---|---|
| Hazard | pluie 24 h | `min(pluie / 150, 1)` | plus de pluie, plus d'eau à évacuer ; 150 mm = référence « maximale » |
| Vulnerability | altitude basse | `1 − min(alt / 20 m, 1)` | l'eau s'accumule dans les points bas |
| | pente faible | `1 − min(pente / 0,5°, 1)` | terrain plat = eau qui stagne (Dakar est très plat) |
| | historique | valeur 0-1 | une zone déjà inondée l'est souvent à nouveau |
| | drainage insuffisant | `1 − qualité` | un mauvais drainage aggrave l'accumulation |
| Exposure | population | min-max (min → 95e centile) | plus de personnes concernées |
| | infrastructures | hôpitaux×3 + écoles×1 + marchés×1,5, puis min-max | importance relative d'un service essentiel |
| | routes | min-max | accès et circulation |

Le 95e centile évite qu'une valeur extrême écrase toutes les autres.

## Pondération initiale

| Bloc | Poids | Justification |
|---|---|---|
| Hazard | 0,40 | sans pluie, pas d'inondation pluviale : l'aléa pilote le scénario |
| Vulnerability | 0,35 | détermine *où* l'eau cause des problèmes |
| Exposure | 0,25 | détermine *l'ampleur* des conséquences |

Sous-poids : voir `config/risk.yaml`. Les poids sont **relatifs** et normalisés automatiquement (doubler tous les poids ne change rien — testé).

## Méthodes de combinaison

- `weighted_sum` (défaut) : `score = 100 × (wH·H + wV·V + wE·E)`. Simple et explicable. *Limite* : un score non nul même quand l'aléa est faible.
- `multiplicative` : `score = 100 × H × (wV·V + wE·E)/(wV+wE)`. Fidèle à « risque = aléa × conséquences », mais produit des scores plus bas.
- **Garde-fou** : sous `min_rain_mm` (10 mm), score = 0.

## Niveaux (exemple illustratif)

| Score | Niveau |
|---|---|
| 0-20 | faible |
| 21-40 | modéré |
| 41-60 | élevé |
| 61-80 | très élevé |
| 81-100 | critique |

## Validation (à faire avec de vraies données)
Comparer le score aux étendues d'inondation EO4SD : les zones réellement inondées devraient obtenir des scores moyens plus élevés. Tant que cette comparaison n'est pas faite, le score est un **modèle d'expert non validé**.

## Évolution possible
Calibrer les poids (analyse de sensibilité, AHP), puis modèle ML supervisé si l'historique le permet.
