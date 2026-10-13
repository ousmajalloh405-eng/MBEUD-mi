# MBEUD-mi — Évaluation exploratoire EO4SD Dakar 2009

## 1. Objectif

Cette analyse compare le score calculé par MBEUD-mi au recouvrement
spatial des zones expérimentales avec les polygones classés `Flooded`
dans la couche historique de Dakar pour 2009.

Il s'agit d'une analyse descriptive, pas d'une validation prédictive
du risque d'inondation.

## 2. Sources et périmètre

### Couche historique

- Catalogue : Banque mondiale / ESA EO4SD-Urban.
- Jeu : Dakar Flood Extent Maps 2009–2018.
- Ressource utilisée : Flood Extent Map for Dakar 2009.
- URL : https://datacatalog.worldbank.org/search/dataset/0038482/dakar-senegal-flood-extent-maps-2009-2018-esa-eo4sd-urban
- Licence annoncée : CC BY 4.0.
- Format local : Shapefile extrait d'une archive ZIP.
- CRS : WGS 84 / UTM Zone 28N, EPSG:32628.

### Données de MBEUD-mi

- Relief expérimental : `data/processed/terrain_experimental_zones.csv`
- Comparaison des scores : `data/processed/terrain_score_comparison.csv`
- Recouvrement historique : `data/processed/eo4sd_flood_overlap_2009.csv`
- Script d'évaluation : `scripts/evaluate_eo4sd_2009.py`
- Résumé JSON : `data/processed/eo4sd_2009_exploratory_evaluation.json`

L'expérience couvre 862 zones avec altitude et pente exploitables,
soit 43,82 % des 1 967 zones de la grille actuelle.


## 3. Contrôle de la couche historique

La couche contient 636 polygones :
- `Flooded` : 442 ;
- `Water body` : 172 ;
- `Non-flooded` : 22.

Les 636 géométries ont été contrôlées : aucune n'était vide ou invalide.
Seuls les polygones `Flooded` sont utilisés pour calculer le recouvrement.

Le champ `AREA` correspond à la superficie géométrique calculée.
Son unité paraît être le mètre carré, mais cela reste à confirmer
dans la documentation de la source.

## 4. Méthode

Pour chaque zone expérimentale :
1. La cellule est transformée vers le CRS EPSG:32628.
2. Les polygones `Flooded` sont fusionnés.
3. L'intersection entre la cellule et les polygones est calculée.
4. Le pourcentage de recouvrement est calculé à partir des superficies.
5. Le score MNE est comparé au recouvrement historique.

Le score utilise une pluie hypothétique de 120 mm, qui ne représente
pas une mesure météorologique de l'épisode de 2009.


## 5. Résultats

Nombre de zones comparées : 862.

| Recouvrement historique | Zones | Score MNE moyen | Score MNE médian |
|---|---:|---:|---:|
| Moins de 1 % | 606 | 61,716 | 61,90 |
| Au moins 1 % | 256 | 63,599 | 63,40 |
| Au moins 10 % | 84 | 64,412 | 64,25 |

Corrélation de Spearman entre le score MNE et le pourcentage de
recouvrement : **0,0759**.

L'association observée est très faible. Les scores moyens sont
légèrement plus élevés dans les groupes ayant davantage de
recouvrement historique, mais ce résultat ne prouve pas que
le modèle prédit correctement les inondations.

## 6. Limites et interprétation

- La population, les infrastructures, le drainage et l'historique des inondations restent synthétiques.
- Les poids et seuils du modèle sont des hypothèses non calibrées.
- Les 862 zones analysées représentent 43,82 % de la grille initiale.
- La pluie de 120 mm est hypothétique et ne reconstitue pas la météo de 2009.
- L'absence de recouvrement avec les polygones `Flooded` ne prouve pas qu'une zone n'a jamais été inondée.
- La couche historique n'est pas considérée comme un inventaire exhaustif.
- Cette analyse ne démontre ni causalité ni capacité prédictive.
- Aucun intervalle de confiance ni test de significativité n'a été calculé.

**Conclusion :** l'association entre le score et le recouvrement historique de 2009 est très faible (Spearman = 0,0759). Les résultats montrent les limites actuelles du prototype et la nécessité d'améliorer les données et de poursuivre l'évaluation.

## 7. Reproduction

Depuis la racine du dépôt, avec l'environnement Python activé, exécuter :

    PYTHONPATH=. python scripts/evaluate_eo4sd_2009.py

Le script produit un résumé JSON et deux tableaux CSV dans `data/processed/`.

Le GeoJSON de démonstration et les scores du dashboard ne sont pas remplacés par cette évaluation expérimentale.
