# PROJET_URBANWATT

Base PostgreSQL qui regroupe les clients, leurs véhicules, les stations et bornes de recharge, les sessions de recharge et leurs paiements, ainsi que le suivi de maintenance (incidents, interventions, techniciens).
Vous retrouverez dans "Documentation.pdf" tout ce qui concerne justification de nos choix, captures d'écran prouvant le fonctionnement de la base de données, captures d'écran des résultats des requêtes données ainsi que les procédures de sauvegardes et de restauration.

## Sommaire

1. [Arborescence du projet](#arborescence-du-projet)
2. [Guide d'accès aux répertoires](#guide-daccès-aux-répertoires)
3. [Les données sources](#les-données-sources)
5. [Ordre de chargement](#ordre-de-chargement)

## Arborescence du projet

```
projet-urbanwatt/
├── README.md
│       
├── docs/
│   ├── Documentation.pdf
│   ├── Urbanwatt_schema.jpg
│   └── DictionnaireDonnées.xlsx
│
├── infra/
│    ├──  compose.yaml
│    └──  env.example
│              
└── sql/
    ├── 01_schema.sql
    ├── 01.1.rôle.sql
    ├── 02_verification.sql
    └── 03_requetes.sql

```


## Guide d'accès aux répertoires

| Répertoire | Contenu | Quand l'utiliser |
|---|---|---|
| `docs/` | La documentation du modèle : cardinalités, règles de gestion et hypothèses à valider. | Pour comprendre pourquoi les tables sont liées de cette façon. |
| `infra/` | Fichier compose du conteneur Docker et exemple du .env de configuration | Pour mettre en place le projet de votre côté |
| `sql/` | Les scripts SQL, numérotés dans leur ordre d'exécution. | Pour créer la base, importer les données puis contrôler leur cohérence. |

### Détail du répertoire `sql/`

| Fichier | Rôle |
|---|---|
| `01_schema.sql` | Crée les neuf tables avec leurs clés primaires, clés étrangères, contraintes (`UNIQUE`, `CHECK`) et index. |
| `01.1.role.sql` | Ajouter les rôles des utilisateurs à la base de données  |
| `02_verification.sql` | Requêtes de vérification des tables  |
| `03_requêtes.sql` | Requêtes des questions du slide. |


### Détail du répertoire `docs/`

| Fichier | Rôle |
|---|---|
| `Dictionnaire de données` | Tableau de justification des choix de la base de données |
| `UrbanWatt_Schema.jpg` | Ajouter les rôles des utilisateurs à la base de données  |
| `Documentation.pdf` | Documentation complète du projet + scénario de test + stratégie de sauvegarde |



## Ordre de chargement

Les clés étrangères imposent de charger les tables parentes avant les tables enfants :

1. `client`, `station`, `technicien` (aucune dépendance)
2. `vehicule` (dépend de `client`) et `borne` (dépend de `station`)
3. `session_recharge` (dépend de `borne` et `vehicule`) et `incident` (dépend de `borne`)
4. `paiement` (dépend de `session_recharge`) et `intervention` (dépend de `incident` et `technicien`)
