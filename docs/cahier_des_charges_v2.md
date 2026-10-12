# Cahier des charges V2 — MBEUD-mi

## 1. Vision

Faire évoluer **MBEUD-mi** vers une plateforme géospatiale d'aide à l'anticipation et à la coordination face aux inondations urbaines au Sénégal. Le centre décisionnel souhaité associera météo, terrain, occupation du sol, exposition des personnes et infrastructures, historique d'inondation et état des moyens disponibles.

Cette vision est une cible de développement. Le projet actuel est un prototype : ses scores principaux reposent sur des données synthétiques. Il ne constitue ni un service officiel d'alerte, ni un outil validé pour ordonner des évacuations ou mobiliser des secours.

## 2. Utilisateurs visés

- Agents d'analyse et équipes techniques.
- Collectivités territoriales et services d'assainissement.
- Protection civile et services de secours, sous réserve de validation institutionnelle et de procédures d'intégration convenues.
- Responsables d'infrastructures et partenaires de recherche.

Les besoins, responsabilités, autorisations d'accès et processus de validation doivent être confirmés avec les organisations concernées avant tout usage opérationnel.

## 3. Principes non négociables

1. **Traçabilité** : chaque jeu de données indique son fournisseur, sa date de récupération, son horodatage de validité, sa couverture géographique, ses unités, sa licence et ses limites connues.
2. **Séparation des données** : réel, synthétique, estimé et indisponible ne doivent jamais être mélangés sans indicateur explicite.
3. **Validation avant diffusion** : timestamps, valeurs manquantes, doublons, coordonnées, unités et couverture sont contrôlés avant le calcul du score.
4. **Explicabilité** : afficher les composantes du score, ses hypothèses et le niveau d'incertitude.
5. **Human-in-the-loop** : les recommandations servent à l'analyse. Aucune évacuation, alerte officielle ou commande de matériel n'est déclenchée automatiquement par ce prototype.
6. **Sécurité** : ne pas collecter de données personnelles non nécessaires ; protéger les comptes, secrets, journaux sensibles et interfaces de gestion.
7. **Résilience** : si la source externe est indisponible ou périmée, afficher l'erreur et l'heure de dernière donnée valide. Ne pas transformer silencieusement une valeur ancienne en donnée temps réel.
8. **Évolutions isolées** : le développement V2 se fait dans une branche séparée. La branche `main` et son service public ne changent pas tant que les tests et la validation manuelle ne sont pas terminés.

## 4. Périmètre produit par étapes

### V2.0 — Première donnée météo réelle pour Dakar

- Récupérer par API une prévision horaire de précipitation pour le point de référence configuré à Dakar.
- Fournir une route API explicitement marquée comme donnée de fournisseur, avec horodatage, unités, durée couverte et attribution.
- Contrôler la structure, l'ordre des horaires et les valeurs de précipitation.
- Gérer timeout, erreur fournisseur et réponse invalide avec des erreurs explicites.
- Conserver les pages actuelles du dashboard inchangées jusqu'à ce que la route ait été vérifiée en tests et dans un navigateur.

Cette étape ne fournit **pas** un radar, une prévision d'inondation, une cartographie nationale ni une alerte officielle. Une prévision météo sur un point ne décrit pas à elle seule la pluie sur tout un quartier.

### V2.1 — Provenance et qualité des données

- Standardiser les métadonnées : `source`, `data_origin`, `retrieved_at`, `valid_time`, `units`, `coverage`, `quality_status`.
- Stocker les réponses brutes sans les écraser, puis produire des tables nettoyées et documentées.
- Ajouter des tests de contrats de réponse et des tests simulant les pannes réseau.
- Afficher dans l'interface le fournisseur, l'heure de la dernière mise à jour et les limites de la donnée.
- Prévoir une stratégie de cache et des limites d'appels pour ne pas solliciter le fournisseur à chaque interaction utilisateur.

### V2.2 — Topographie, routes et équipements

- Utiliser le modèle numérique de terrain de Dakar déjà identifié, en indiquant clairement ses zones couvertes et les métadonnées verticales encore à vérifier.
- Ajouter les routes, bâtiments, hôpitaux, écoles, marchés, bassins et stations depuis des sources identifiées et autorisées.
- Conserver la provenance au niveau du jeu de données ; ne pas supposer que les équipements OSM sont exhaustifs ou à jour.
- Calculer les pentes, points bas, intersections et distances avec un système de coordonnées projeté approprié ; documenter les transformations.

### V2.3 — Première carte de risque hybride (pilote Dakar)

- Intégrer des variables réelles dont la qualité et la couverture sont suffisamment documentées.
- Identifier séparément chaque variable synthétique qui reste nécessaire.
- Afficher l'état de couverture et l'incertitude par zone.
- Comparer le modèle aux historiques d'inondations disponibles sur des périodes et emprises compatibles.
- Rendre les hypothèses du modèle modifiables et évaluables.

Cette carte restera expérimentale tant que sa validation n'est pas suffisante. La comparaison EO4SD 2009 déjà documentée présente une corrélation de Spearman très faible (0,0759) dans le scénario testé ; elle ne justifie donc pas de présenter le score comme prédictif.

### V3 — Extension régionale puis nationale

L'extension à Pikine, Guédiawaye, Rufisque, puis à Touba, Kaolack et Saint-Louis dépendra de la disponibilité, de la résolution, de la fréquence et de la qualité des sources pour chaque région. Ne pas transposer sans recalibrage les paramètres d'une zone géographique à l'autre.

### V4+ — Fonctions avancées sous conditions

- Historique animé et données satellitaires/radar : uniquement après identification du produit et de ses conditions d'accès, de licence, de résolution et de fréquence.
- Niveaux de bassins et état des stations : intégration après obtention d'une télémétrie réelle ou d'un processus de mise à jour autorisé.
- Routes coupées et déviations : une donnée de circulation ou de fermeture vérifiée est requise.
- Airflow, stockage objet Bronze/Silver/Gold, Spark/DuckDB et PostGIS comme source principale : à ajouter selon les besoins de volumétrie et de traçabilité, pas simplement pour empiler des technologies.
- SMS/WhatsApp, profils d'assureurs, paiements ou API commerciales : hors du premier MVP ; nécessitent étude de coûts, consentement, sécurité, contrats et support opérationnel.

## 5. Sources : état et prérequis

| Domaine | Source candidate | État du projet / vérification nécessaire |
|---|---|---|
| Prévision météo | Open-Meteo | Première intégration API en développement. Il s'agit d'une prévision fournie par un modèle, pas d'une mesure locale garantie. Attribution et conditions d'utilisation à respecter. |
| Bulletins officiels | ANACIM | À intégrer seulement après validation du mode d'accès, des formats, de la fréquence de mise à jour et des droits de réutilisation. |
| Pluie satellitaire | NASA GPM IMERG | Produit candidat ; vérifier latence, résolution, format et conditions d'accès avant ingestion. |
| Relief Dakar | MNT 5 m de Géo Sénégal | Fichier local existant, couverture partielle des zones du projet et métadonnées verticales à confirmer. |
| Historique des inondations | ESA EO4SD-Urban / catalogue Banque mondiale | Couche historique Dakar 2009 déjà utilisée pour une évaluation exploratoire ; vérifier l'adéquation de la couverture et des dates avant toute comparaison supplémentaire. |
| Voirie et équipements | OpenStreetMap | Couche candidate ; vérifier la complétude, la date d'extraction et la licence d'attribution. |
| Population et limites administratives | ANSD / HDX / services publics | Sources candidates ; sélectionner des versions documentées et compatibles en géographie et en date. |
| Bassins et stations | ONAS / gestionnaires compétents | Données, API et autorisations non confirmées dans le prototype actuel. |

Références de départ :
- Open-Meteo : https://open-meteo.com/en/docs
- Géo Sénégal, MNT Dakar 5 m : https://geosenegal.gouv.sn/Dakar-elevation-5-m.html
- Catalogue EO4SD / Banque mondiale : https://datacatalog.worldbank.org/search/dataset/0038482/dakar-senegal-flood-extent-maps-2009-2018-esa-eo4sd-urban

## 6. Architecture cible

```text
Sources météo / topo / OSM / historiques / équipements
                       |
                       v
            Ingestion et catalogue de sources
                       |
                       v
             Bronze : données brutes datées
                       |
                       v
      Qualité + normalisation + enrichissement spatial
                       |
                       v
       Silver : tables cohérentes et géométries contrôlées
                       |
                       v
       Gold : variables par zone, scénario et horodatage
                       |
             +---------+----------+
             |                    |
             v                    v
      API FastAPI          Analyse / validation
             |
             v
       Dashboard géospatial
```

Technologies envisagées : Python, Pandas, GeoPandas/Shapely, rasterio, PostgreSQL/PostGIS, FastAPI et Streamlit. Airflow, Spark, DuckDB et MinIO/S3 sont des choix de cible qui seront introduits seulement lorsqu'un cas d'usage les justifiera.

## 7. Modèle de risque : exigences à valider

Ne pas appliquer directement la formule `pluie_mm * 0.6 + indice * 0.4` à des unités brutes : les millimètres de pluie ne sont pas une variable normalisée et peuvent produire un score hors de l'échelle 0–100.

La proposition de travail est de calculer des composantes bornées entre 0 et 1 :
- **Aléa (H)** : intensité, cumul et durée de pluie, complétés lorsque disponibles par les facteurs topographiques et hydrologiques.
- **Vulnérabilité (V)** : capacité de drainage, sensibilité locale et autres variables documentées.
- **Exposition (E)** : personnes, routes et équipements potentiellement touchés.

Une forme pondérée peut être évaluée (`Score = 100 × (wH·H + wV·V + wE·E)`, où les poids sont non négatifs et leur somme vaut 1). Les variables, fonctions de normalisation, poids et seuils doivent être documentés, soumis à des tests de sensibilité et calibrés avec des données indépendantes. Cette formule n'est pas encore un modèle validé.

Les couleurs affichées sont des catégories expérimentales jusqu'à validation par les acteurs responsables. Des seuils de pluie seuls ne suffisent pas pour déclencher une alerte rouge ou décider une évacuation.

## 8. API : existant et proposé

### Endpoints existants

- `GET /health`
- `GET /zones`
- `GET /risk?rain_mm=`
- `GET /risk/{zone_id}`
- `GET /forecast?total_mm=` — courbe **synthétique**
- `GET /alerts?rain_mm=` — alertes de simulation
- `POST /simulation`
- `GET /recommendations`

### Nouvelle route expérimentale en développement

- `GET /api/v1/weather/forecast` — prévision horaire Open-Meteo au point de référence Dakar ; attribuée, contrôlée et séparée du score de risque synthétique.

### Routes futures, à définir après stabilisation du modèle

- `GET /api/v1/zones/status`
- `GET /api/v1/alerts/critical`
- `GET /api/v1/resources/status`

Ne pas employer le même mot « alerte » pour une simulation algorithmique, une information météo de fournisseur et une alerte officiellement validée sans les distinguer dans l'API et l'interface.

## 9. Critères d'acceptation du premier incrément

- Une route retourne les données du fournisseur avec l'attribution, l'horodatage, les unités, la couverture horaire et la mention de limites.
- Le cumul annoncé correspond exactement aux heures retournées et sa couverture est explicite.
- Une panne réseau, une réponse invalide ou des valeurs rejetées produisent une erreur visible et testée, sans retour silencieux aux données synthétiques.
- Les tests ne dépendent pas d'une connexion Internet : la réponse du fournisseur est simulée dans les tests.
- La provenance météo et les scores synthétiques restent distinguables.
- La branche de production et le service public existant restent inchangés avant validation.

## 10. Mesures de réussite

Les objectifs quantitatifs tels que « intervenir 4 à 6 heures avant le pic pluvieux », « réduire les coûts » ou « améliorer les temps de réponse opérationnels » sont des **hypothèses d'impact**, pas des résultats établis. Ils doivent être mesurés avec un protocole, une période de référence, des jeux de données validés et des partenaires opérationnels.

Mesures techniques possibles : disponibilité, délai de rafraîchissement, complétude des données, taux d'échec des sources, proportion des zones avec des données réelles, précision/rappel sur un historique indépendant, faux positifs/faux négatifs et stabilité du classement quand les paramètres changent.

## 11. Prochaines actions

1. Tester la nouvelle route météo avec des tests unitaires indépendants du réseau.
2. Exécuter les tests de l'ensemble du dépôt sur la branche de développement.
3. Vérifier manuellement la route sur l'environnement de développement lorsque l'accès externe est disponible.
4. Décider avec les résultats si la donnée météo peut être exposée dans un nouvel onglet du dashboard.
5. Ne fusionner vers `main` et ne redéployer le service public qu'après validation explicite.
