# Mise en ligne de MBEUD-mi (démo)

## Déploiement sur Render

Le dépôt inclut un Blueprint `render.yaml` et une image Docker dédiée (`docker/Dockerfile.platform`) qui lancent l'API FastAPI et le dashboard Streamlit dans un seul service web.

1. Ouvrir https://dashboard.render.com/ et se connecter ou créer un compte.
2. Choisir **New → Blueprint**.
3. Connecter GitHub si nécessaire, puis sélectionner `ousmajalloh405-eng/MBEUD-mi`.
4. Vérifier les paramètres détectés depuis `render.yaml`, puis lancer le déploiement.
5. À la fin, ouvrir l'URL publique du service Render. Le dashboard Streamlit doit s'afficher. L'API est accessible depuis le conteneur à `http://127.0.0.1:8000`; sa documentation Swagger n'est pas exposée publiquement dans cette configuration.

Le script de démarrage attend que `/health` réponde avant de démarrer Streamlit. Le contrôle de santé public utilise `/_stcore/health`.

## Tester après déploiement

- Ouvrir l'URL publique et naviguer entre Overview, Risk Map, Forecast, Zones, Simulation, Resources et Alerts.
- Vérifier que les métriques s'affichent et que la carte est chargée.
- Si le service échoue au démarrage, consulter les journaux de build et de runtime dans Render.

## Limites importantes

- Il s'agit d'une **démo expérimentale**, pas d'un service opérationnel d'alerte aux inondations.
- Le dashboard utilise le jeu principal de données synthétiques. Les résultats ne sont pas des prévisions officielles et ne doivent pas guider seuls une décision d'urgence.
- Le plan gratuit de l'hébergeur peut mettre le service en veille après une période d'inactivité et entraîner un délai au premier accès.
- Le fichier raster MNT et les fichiers de traitement locaux ne sont pas inclus dans Git, conformément au `.gitignore`. Le lancement du dashboard ne dépend pas de ces fichiers.
- Aucun secret ni mot de passe de base de données n'est requis pour cette démo groupée. Ne jamais publier de clés ou mots de passe dans Git.

## Architecture du service de démo

```text
Navigateur
   |
   v
Streamlit (port fourni par Render)
   |
   v
FastAPI (127.0.0.1:8000, interne au conteneur)
   |
   v
data/synthetic/zones.geojson
```
