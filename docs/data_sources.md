# MBEUD-mi — Registre des sources de données

Dernière vérification des catalogues : 2026-10-12.

Ce document distingue :
- les données déjà présentes dans le projet ;
- les sources officielles ou catalogues identifiés ;
- les sources candidates qui restent à intégrer ou à vérifier.

**Important :** identifier une source sur un catalogue ne signifie pas que ses données ont été téléchargées, intégrées ou validées.

## 1. Données déjà présentes dans le projet

### 1.1 Modèle numérique de terrain de Dakar — MNT 5 m

| Champ | Information |
|---|---|
| Source locale | `data/raw/Dakar_MNE_5m.tif` |
| Catalogue | [Géo Sénégal — Dakar élévation 5 m](https://geosenegal.gouv.sn/Dakar-elevation-5-m.html) |
| Organisme source indiqué | ANAT |
| Format annoncé | GeoTIFF |
| Résolution spatiale nominale | 5 m |
| Échelle du produit annoncée | 1:2 000 |
| CRS du fichier local | EPSG:32628 |
| Dimensions constatées | 5 088 × 3 697 pixels |
| NoData du fichier | -9999 |
| Licence de réutilisation | À vérifier avant redistribution |
| Référentiel vertical | Non confirmé |
| Précision verticale | Non documentée dans les métadonnées locales |

**Utilisation dans MBEUD-mi**

- Extraction de l'altitude au centre des zones.
- Calcul d'une pente locale à partir des pixels voisins.
- Diagnostic de couverture et détection des valeurs NoData.
- Construction d'un sous-ensemble expérimental de zones disposant d'un relief calculable.

**Diagnostic actuel**

- Zones de la grille : 1 967.
- Zones avec altitude et pente disponibles : 862.
- Centres hors couverture : 1 053.
- Centres situés sur des pixels NoData : 52.
- Couverture exploitable : 43,82 %.

Ces résultats décrivent la grille actuelle du prototype, et non la couverture officielle de l'ensemble de Dakar.

La résolution spatiale de 5 m ne garantit pas une précision verticale de 5 m. Les unités verticales, le référentiel vertical et la précision doivent être confirmés dans une documentation technique adaptée.

Fichiers produits :

- `data/processed/elevation_coverage.csv`
- `data/processed/terrain_experimental_zones.csv`
- `data/processed/terrain_experimental_metadata.json`
- `data/processed/terrain_score_comparison.csv`

Le raster source est volumineux. Avant de publier le dépôt, vérifier sa licence et décider s'il doit être téléchargé séparément plutôt que versionné dans Git.

### 1.2 Données synthétiques de démonstration

| Champ | Information |
|---|---|
| Générateur | `src/processing/synthetic.py` |
| Fichier généré | `data/synthetic/zones.geojson` |
| Nombre de zones | 1 967 |
| Origine déclarée | `SYNTHETIC DATA — FOR DEMONSTRATION ONLY` |

Les variables synthétiques comprennent notamment :

- l'altitude et la pente d'origine ;
- l'historique des inondations ;
- la qualité du drainage ;
- la population et les infrastructures ;
- la longueur des routes ;
- le polygone terrestre approximatif et les localités indicatives.

Le GeoJSON reste utilisé par le pipeline de démonstration. Il n'a pas été remplacé par le sous-ensemble expérimental.

### 1.3 Jeu expérimental à données mixtes

Le fichier `data/processed/terrain_experimental_zones.csv` utilise le relief issu du MNT lorsque l'altitude et la pente sont disponibles. Les autres variables demeurent synthétiques.

Le fichier de comparaison permet de comparer les scores obtenus avec le relief synthétique et le relief issu du MNT sur les mêmes 862 zones.

**Ces résultats sont une analyse de sensibilité du modèle, pas une validation de la capacité à prédire les inondations réelles.**

---

## 2. Sources prioritaires à intégrer

### 2.1 Étendues d'inondation historiques — ESA EO4SD-Urban

| Champ | Information |
|---|---|
| Catalogue | [Dakar Flood Extent Maps 2009–2018](https://wbwaterdata.org/dataset/dakar-senegal-flood-extent-maps-2009-2018-esa-eo4sd-urban) |
| Format annoncé | Shapefile dans des archives ZIP |
| Période | 2009–2018 |
| Licence annoncée | CC BY 4.0 |
| Statut dans MBEUD-mi | Source identifiée, intégration à réaliser |

La fiche du catalogue indique six étendues d'inondation issues d'imagerie optique à haute résolution et sept étendues issues de l'interprétation visuelle de données à très haute résolution disponibles dans Google Earth.

**Utilisation envisagée**

- Examiner les géométries et les attributs fournis.
- Vérifier les dates, la couverture géographique et le système de coordonnées.
- Documenter la méthode de détection et les limites de chaque couche.
- Calculer les recouvrements entre les zones historiques observées et la grille du projet.
- Évaluer le comportement du score face aux observations disponibles.

Avant de parler de validation, vérifier l'indépendance des données, leur qualité et leur compatibilité temporelle avec les variables utilisées par le modèle.

### 2.2 Carte d'aléa d'inondation — ESA EO4SD-Urban

| Champ | Information |
|---|---|
| Catalogue | [Dakar Flood Hazard Map](https://energydata.info/en/dataset/dakar-senegal-flood-hazard-map-esa-eo4sd-urban) |
| Format annoncé | SHP ZIP |
| Licence annoncée | CC BY 4.0 |
| Statut dans MBEUD-mi | Source identifiée, intégration à réaliser |

La fiche décrit une classification qualitative de l'aléa en trois niveaux à partir des occurrences d'inondations sur une période historique. Elle mentionne aussi les menaces liées aux marées et à l'érosion côtière, estimées à partir de rapports et de l'interprétation de changements du littoral.

Cette carte pourra servir à une comparaison exploratoire. Elle ne doit pas être considérée automatiquement comme une vérité terrain indépendante du score.

### 2.3 Carte de risque — ESA EO4SD-Urban

| Champ | Information |
|---|---|
| Catalogue | [Dakar Flood Risk Map](https://wbwaterdata.org/dataset/groups/dakar-senegal-flood-risk-map-esa-eo4sd-urban) |
| Licence annoncée | CC BY 4.0 |
| Statut dans MBEUD-mi | Source identifiée, intégration à réaliser |

Une comparaison avec cette carte devra tenir compte des méthodes, des périodes et des variables utilisées pour produire la carte de référence. Une ressemblance entre deux cartes ne constitue pas, à elle seule, une validation indépendante.

---

## 3. Autres sources candidates

| Source | Données recherchées | Statut et précautions |
|---|---|---|
| [ANSD — RGPH-5 2023](https://www.ansd.sn/recensement/rgph-5-2023) | Population et statistiques par localité | Format précis, granularité, licence et conditions de réutilisation à vérifier. |
| [Géo Sénégal — occupation du sol de Dakar](https://www.geosenegal.gouv.sn/occupation-du-sol-dakar-nd-28-xiii.html) | Occupation du sol 2010, 2015 et 2020 | Catalogue indiquant des fichiers SHP, avec ANAT/CSE/ANSD comme sources. Vérifier la tuile exacte, les classes, la licence et la couverture utile. |
| [HDX — Senegal geodatabase](https://data.humdata.org/dataset/b94a55d0-0b8e-4458-9499-8bbc6987d396) | Limites administratives, localités, routes, hydrologie et infrastructures | Jeu ancien signalé comme datant de 2017 ; vérifier les attributs, la licence et l'actualité. |
| [OpenStreetMap](https://www.openstreetmap.org/) | Routes, bâtiments, hôpitaux, écoles et autres infrastructures cartographiées | Vérifier les objets disponibles et leur qualité locale. Respecter l'attribution et les obligations de la licence ODbL. |
| [WorldPop](https://www.worldpop.org/) | Population en grille | Vérifier la version, l'année, la résolution et la licence du produit choisi. |
| [CHIRPS](https://www.chc.ucsb.edu/data/chirps) | Pluies historiques | Vérifier la période, la résolution spatiale et temporelle, ainsi que les conditions d'utilisation. |
| [GPM IMERG](https://gpm.nasa.gov/data/imerg) | Estimations de précipitations par satellite | Vérifier le produit, les dates et la résolution avant intégration. |
| [Copernicus Data Space](https://dataspace.copernicus.eu/) | Données satellitaires et produits géospatiaux | Choisir un produit adapté ; ne pas le traiter comme une source déjà intégrée. |
| [ANACIM](https://www.anacim.sn/) | Bulletins, observations et informations météorologiques | Source institutionnelle à consulter. Aucune API ouverte n'est considérée comme intégrée à ce stade. |
| [Open-Meteo](https://open-meteo.com/) | Données météo et prévisions | Vérifier les conditions actuelles d'utilisation du service et la licence correspondant aux données retenues avant toute publication ou réutilisation. |

### Documents de contexte sur les inondations

Le catalogue [Inondations-Dakar.org](https://inondations-dakar.org/dataset?q=inondation%20%C3%A0%20dakar) référence des cartes et rapports en PDF sur les inondations à Dakar, notamment une carte de zones touchées détectées par satellite.

Ces documents peuvent aider à comprendre le contexte et à rechercher des références historiques. Toutefois, une ressource PDF dont la licence n'est pas spécifiée ne doit pas être convertie et redistribuée automatiquement comme un jeu de données ouvert.

---

## 4. Variables encore synthétiques

À ce stade, les variables suivantes restent synthétiques dans le jeu expérimental :

- population ;
- nombre d'hôpitaux ;
- nombre d'écoles ;
- nombre de marchés ;
- longueur des routes ;
- historique des inondations ;
- qualité du drainage.

L'altitude et la pente du sous-ensemble expérimental proviennent du raster, mais cela ne rend pas automatiquement les autres variables réelles.

Les données sur le fonctionnement des pompes, les capacités réelles de drainage, la circulation en temps réel et les hauteurs d'eau ne sont pas considérées comme disponibles dans le projet tant qu'une source exploitable n'a pas été trouvée et intégrée.

---

## 5. Règles d'intégration et de traçabilité

Avant d'intégrer une source :

1. Enregistrer l'URL, le producteur, la date d'accès, la licence et les conditions de réutilisation.
2. Conserver la source brute séparément des données transformées.
3. Vérifier le format, le système de coordonnées, les dates, la couverture et les champs disponibles.
4. Contrôler les doublons, valeurs manquantes, géométries invalides et unités.
5. Documenter les transformations et le nombre d'enregistrements avant et après chaque étape.
6. Conserver la provenance de chaque variable, et non seulement une étiquette générale pour le dataset.
7. Ne pas remplacer une donnée manquante par une valeur synthétique sans l'indiquer explicitement.
8. Ne pas présenter les scores comme une prévision validée avant une évaluation indépendante.

### Priorité de développement

La prochaine intégration recommandée est celle des **étendues d'inondation historiques ESA EO4SD-Urban de Dakar**, car le catalogue référence des archives SHP pour plusieurs années et une licence CC BY 4.0.

La première étape consistera à récupérer une archive, inspecter ses fichiers, identifier ses attributs et vérifier sa couverture. Ensuite seulement, nous déciderons comment la rattacher à la grille de MBEUD-mi.
