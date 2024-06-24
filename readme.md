# Projet de Scraping d'Offres d'Emploi

Ce projet vise à récupérer des données sur les offres d'emploi depuis plusieurs plateformes de recrutement en ligne. Il utilise le scraping web pour extraire les informations pertinentes et les sauvegarder localement sous forme de fichiers JSON.

## Plateformes Supportées

- Indeed
- APEC
- HelloWork
- LinkedIn
- JobUp
- Pôle Emploi

## Dépendances

Le projet utilise Python et plusieurs bibliothèques externes, notamment :

- `pandas` pour la manipulation des données.
- `json` pour la lecture et l'écriture de fichiers JSON.
- `os` pour les opérations liées au système de fichiers.
- `datetime` pour gérer les dates.
- `concurrent.futures` pour l'exécution parallèle.

## Structure du Projet

- `scrapers/`: Contient les modules de scraping pour chaque plateforme.
- `utils/`: Contient des modules utilitaires, comme le nettoyage de texte et l'ajout d'informations de contact.
- `json/`: Dossier cible pour les fichiers JSON générés.
- `img/`: Dossier pour stocker les images récupérées (logos, etc.).
- `db/`: Contient des fichiers JSON de configuration, comme la liste des catégories d'emploi à scraper.
- `main.py`: Script principal qui orchestre le scraping.

## Fonctionnement

1. Le script lit la liste des catégories d'emploi depuis `db/categorie.json`.
2. Pour chaque catégorie, il appelle les fonctions de scraping de chaque plateforme.
3. Les données récupérées sont nettoyées et sauvegardées dans le dossier `json/`.

## Utilisation

Pour exécuter le script, assurez-vous d'avoir Python installé sur votre machine, puis installez les dépendances nécessaires :

```bash
pip install pandas beautifulsoup4 selenium
```
