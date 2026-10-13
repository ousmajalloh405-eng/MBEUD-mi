# Décisions d'architecture (ADR courts)

| # | Décision | Raison | Alternative écartée |
|---|---|---|---|
| 1 | Grille régulière de 500 m comme unité de calcul, regroupement par secteur à l'affichage | Précision pour le calcul, lisibilité pour le décideur | Communes seules : trop grossier, dilue le risque |
| 2 | Données synthétiques d'abord, réelles ensuite | Système de bout en bout tôt, moins de blocages | Attendre les vraies données |
| 3 | **MVP : l'API lit un fichier GeoJSON** ; PostGIS fourni (schéma + chargeur) mais pas encore lu par l'API | Limiter la complexité du premier livrable | API sur PostGIS dès le départ (prévu V3) |
| 4 | Pas d'Airflow ni de Kafka dans le MVP | Aucun besoin réel (pas de flux récurrent ni de temps réel) | « Technology soup » |
| 5 | Pas de GeoPandas dans le MVP | Shapely suffit pour une grille ; GeoPandas devient utile pour lire les shapefiles EO4SD (V3) | L'ajouter par principe |
| 6 | Score explicable (3 blocs conservés) avant tout ML | Pas de données d'entraînement ; défendable devant un jury | ML immédiat |
| 7 | Dashboard sans calcul, via l'API | Remplaçable (mobile) sans toucher au moteur | Calculs dans Streamlit |
| 8 | Vocabulaire « recommandation » / « priorité proposée » | Le système n'a aucune autorité opérationnelle | « Ordre automatique » |
| 9 | Port PostgreSQL 5433 sur la machine hôte | Éviter le conflit avec un PostgreSQL local | 5432 |
