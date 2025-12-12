# MUDSTAR LOD Lights - Code Structure

## Architecture

L'addon est maintenant organisé de manière modulaire pour faciliter la maintenance et l'évolution future.

### Structure des fichiers

```
MUDSTAR-LODLIGHTS/
│
├── __init__.py              # Point d'entrée principal de l'addon
│                           # Initialise et enregistre tous les modules
│
└── py/                     # Modules Python
    ├── properties.py       # Définition des propriétés et PropertyGroups
    ├── operators.py        # Opérateurs d'import/export
    └── ui.py              # Interfaces utilisateur (panels)
```

## Modules

### `__init__.py` (racine)
- **Rôle** : Point d'entrée de l'addon Blender
- **Contenu** :
  - `bl_info` : Métadonnées de l'addon
  - `register()` : Enregistre tous les modules
  - `unregister()` : Désenregistre tous les modules
- **Import** : Importe et coordonne tous les sous-modules

### `py/properties.py`
- **Rôle** : Définition des propriétés personnalisées
- **Classes** :
  - `MUDSTAR_PG_LodLightSettings` : PropertyGroup pour les paramètres LOD
- **Propriétés** :
  - Intensité, couleur, distance LOD
  - Falloff, falloff exponent
  - Corona intensity, time flags
  - Hash value

### `py/operators.py`
- **Rôle** : Logique d'import/export
- **Classes** :
  - `MUDSTAR_OT_ImportLodLights` : Import depuis GTA V ymap.xml ou JSON
  - `MUDSTAR_OT_ExportLodLights` : Export vers GTA V ymap.xml (LOD + Distant)
- **Fonctionnalités** :
  - Parsing XML des fichiers GTA V
  - Création automatique des collections
  - Génération des fichiers lodlights et distlodlights
  - Gestion des propriétés GTA V (hash, falloff, corona, etc.)

### `py/ui.py`
- **Rôle** : Interface utilisateur
- **Classes** :
  - `MUDSTAR_PT_LodLightsPanel` : Panel principal "M*LODLights"
- **Affichage** :
  - Informations sur la lumière sélectionnée
  - Propriétés Blender (intensité, couleur)
  - Propriétés GTA V (falloff, corona, hash, etc.)
  - Boutons Import/Export

## Flux de travail

### Import
1. Utilisateur clique sur "Import" dans le panel
2. Sélectionne un fichier `.ymap.xml`
3. `MUDSTAR_OT_ImportLodLights` :
   - Parse le XML
   - Charge les positions depuis le parent si disponible
   - Crée une collection avec le nom du fichier
   - Crée les objets lumière dans Blender
   - Stocke les propriétés GTA V comme custom properties

### Export
1. Utilisateur clique sur "Export" dans le panel
2. Sélectionne un emplacement de sauvegarde
3. `MUDSTAR_OT_ExportLodLights` :
   - Récupère toutes les lumières LOD
   - Détermine le nom depuis la collection
   - Calcule les extents
   - Génère `*_lodlights.ymap.xml` (données LOD)
   - Génère `*_distlodlights.ymap.xml` (positions + couleurs RGBI)

## Avantages de la structure modulaire

1. **Séparation des responsabilités** : Chaque module a un rôle clair
2. **Maintenabilité** : Facile de trouver et modifier le code
3. **Extensibilité** : Simple d'ajouter de nouvelles fonctionnalités
4. **Testabilité** : Modules indépendants plus faciles à tester
5. **Lisibilité** : Code organisé et documenté

## Développement futur

Pour ajouter de nouvelles fonctionnalités :

- **Nouvelles propriétés** → `py/properties.py`
- **Nouveaux opérateurs** → `py/operators.py`
- **Nouveaux panels** → `py/ui.py`
- **Nouveaux modules** → Créer dans `py/` et ajouter à `__init__.py`

## Convention de nommage

- **Préfixe** : `MUDSTAR_` pour toutes les classes
- **Type** : `PT` (Panel), `OT` (Operator), `PG` (PropertyGroup)
- **Nom court** : Panel affiché comme "M*LODLights" pour l'interface utilisateur
- **Nom complet** : "MUDSTAR LOD Lights" pour le nom officiel de l'addon
