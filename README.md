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
│   └── Urbanwatt_schema.jpg
├── app/
│    ├──
│
├── infra/
│    └── compose.yaml
│             
└── sql/
    ├── 01_schema.sql
    ├── 02_verification.sql
    └── 03_requetes.sql

```


## Guide d'accès aux répertoires

| Répertoire | Contenu | Quand l'utiliser |
|---|---|---|
| `data/raw/` | Les neuf fichiers CSV d'origine, non modifiés. Séparateur `;`, encodage UTF-8, première ligne = en-têtes. | Pour importer les données ou vérifier une valeur à la source. Ne pas modifier ces fichiers. |
| `docs/` | La documentation du modèle : cardinalités, règles de gestion et hypothèses à valider. | Pour comprendre pourquoi les tables sont liées de cette façon. |
| `docs/schema/` | Le schéma de la base (MCD/MLD) avec les clés primaires, les clés étrangères et les cardinalités. | Pour avoir une vue d'ensemble avant d'écrire une requête. |
| `sql/` | Les scripts SQL, numérotés dans leur ordre d'exécution. | Pour créer la base, importer les données puis contrôler leur cohérence. |

### Détail du répertoire `sql/`

| Fichier | Rôle |
|---|---|
| `01_schema.sql` | Crée les neuf tables avec leurs clés primaires, clés étrangères, contraintes (`UNIQUE`, `CHECK`) et index. |
| `02_verification.sql` | Requêtes de vérification des tables  |
| `03_requêtes.sql` | Requêtes des questions du slide. |

## Les données sources

| Fichier | Table | Lignes | Contenu |
|---|---|---|---|
| `clients.csv` | `client` | 15 000 | Clients inscrits |
| `vehicules.csv` | `vehicule` | 18 000 | Véhicules, rattachés à un client |
| `stations.csv` | `station` | 120 | Sites de recharge |
| `bornes.csv` | `borne` | 600 | Bornes, rattachées à une station |
| `sessions_recharge.csv` | `session_recharge` | 250 000 | Recharges d'un véhicule sur une borne |
| `paiements.csv` | `paiement` | 217 300 | Paiements, rattachés à une session |
| `incidents.csv` | `incident` | 5 000 | Incidents signalés sur une borne |
| `interventions.csv` | `intervention` | 4 162 | Interventions sur un incident, réalisées par un technicien |
| `techniciens.csv` | `technicien` | 120 | Techniciens de maintenance |


## Ordre de chargement

Les clés étrangères imposent de charger les tables parentes avant les tables enfants :

1. `client`, `station`, `technicien` (aucune dépendance)
2. `vehicule` (dépend de `client`) et `borne` (dépend de `station`)
3. `session_recharge` (dépend de `borne` et `vehicule`) et `incident` (dépend de `borne`)
4. `paiement` (dépend de `session_recharge`) et `intervention` (dépend de `incident` et `technicien`)
