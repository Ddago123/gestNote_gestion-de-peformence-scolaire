# 📚 GestNote — Système de Gestion des Performances Scolaires

## 📋 Vue d'ensemble du projet

**GestNote** est une application web complète de gestion et d'analyse des performances scolaires destinée aux établissements éducatifs. Elle permet aux administrateurs, directeurs et responsables pédagogiques de centraliser, analyser et suivre les performances des élèves à travers des visualisations intuitives, des alertes automatiques et des fiches détaillées.

---

## 🎯 Objectifs du projet

1. **Centraliser les données scolaires** : Unifier l'import et le stockage des notes, élèves et coefficients
2. **Automatiser le suivi pédagogique** : Générer des alertes et indices pour détecter les élèves en difficulté
3. **Visualiser les tendances** : Afficher des courbes de progression/régression par élève et matière
4. **Faciliter la gestion** : Interface intuitive pour administrateurs non-techniques
5. **Assurer la qualité des données** : Validation et rapports de cohérence lors des imports

---

## 📁 Architecture du système

### Structure du projet
```
gestenote/
├── app/                          # Application Flask
│   ├── app.py                    # Backend principal (API REST + logique métier)
│   ├── scolaire.db              # Base de données SQLite (créée automatiquement)
│   ├── start.sh                 # Script de démarrage
│   ├── README.md                # Documentation initiale
│   ├── templates/
│   │   └── index.html           # Interface web unique
│   └── static/
│       ├── css/style.css        # Feuille de styles
│       └── js/app.js            # Logique frontend (API calls, DOM, graphiques)
│
├── listes_classe/               # Fichiers CSV des listes d'élèves par niveau
│   ├── Classe_6eme.csv
│   ├── Classe_5eme.csv
│   ├── Classe_4eme.csv
│   ├── Classe_3eme.csv
│   ├── Classe_2nde.csv
│   ├── Classe_1ere_A.csv
│   ├── Classe_1ere_C.csv
│   ├── Classe_1ere_D.csv
│   ├── Classe_Tle_A.csv
│   ├── Classe_Tle_C.csv
│   └── Classe_Tle_D.csv
│
├── notes_*.csv                  # Fichiers de notes (format: matricule, nom_eleve, note, date)
├── test_eleves.csv              # Fichier de test pour import élèves
├── randomize_notes.py           # Utilitaire pour générer des notes aléatoires (tests)
└── PROJECT_BRIEF.md             # Ce fichier
```

### Stack technologique

**Backend :**
- Framework : Flask (Python)
- Base de données : SQLite3
- Analyse de données : Pandas, NumPy
- Visualisation : Scipy (interpolation spline)

**Frontend :**
- HTML5 + CSS3 + JavaScript vanilla
- Graphiques : Chart.js ou Plotly (à intégrer)
- Communication : Fetch API (JSON)

**Déploiement :**
- Environnement : Python 3.8+
- Dépendances : flask, pandas, scipy, numpy

---

## 🏛️ Modèle de données

### 1. **Entité : AnneesScolaires**
```
┌─────────────────────────────────┐
│ AnneesScolaires                 │
├─────────────────────────────────┤
│ id (INT, PK)                    │
│ annee (VARCHAR, ex: 2025-2026)  │
│ active (BOOL)                   │
│ date_creation (DATETIME)        │
└─────────────────────────────────┘
```

### 2. **Entité : Classes**
```
┌─────────────────────────────────┐
│ Classes                         │
├─────────────────────────────────┤
│ id (INT, PK)                    │
│ annee_id (INT, FK)              │
│ nom (VARCHAR, ex: Terminale S)  │
│ niveau (VARCHAR, ex: Tle)       │
│ date_creation (DATETIME)        │
└─────────────────────────────────┘
```

### 3. **Entité : Eleves**
```
┌─────────────────────────────────┐
│ Eleves                          │
├─────────────────────────────────┤
│ id (INT, PK)                    │
│ classe_id (INT, FK)             │
│ matricule (VARCHAR, unique)     │
│ nom (VARCHAR)                   │
│ prenom (VARCHAR)                │
│ date_naissance (DATE)           │
│ date_import (DATETIME)          │
└─────────────────────────────────┘
```

### 4. **Entité : Matieres**
```
┌─────────────────────────────────┐
│ Matieres                        │
├─────────────────────────────────┤
│ id (INT, PK)                    │
│ classe_id (INT, FK)             │
│ nom (VARCHAR, ex: Français)     │
│ coefficient (INT)               │
└─────────────────────────────────┘
```

### 5. **Entité : Notes**
```
┌─────────────────────────────────┐
│ Notes                           │
├─────────────────────────────────┤
│ id (INT, PK)                    │
│ eleve_id (INT, FK)              │
│ matiere_id (INT, FK)            │
│ note (FLOAT, 0-20)              │
│ date_note (DATE)                │
│ source (VARCHAR, manuel/import) │
│ date_creation (DATETIME)        │
└─────────────────────────────────┘
```

### 6. **Entité : Alertes** (générée automatiquement)
```
┌─────────────────────────────────┐
│ Alertes                         │
├─────────────────────────────────┤
│ id (INT, PK)                    │
│ eleve_id (INT, FK)              │
│ matiere_id (INT, FK)            │
│ type_alerte (VARCHAR)           │
│ severite (INT, 1-5)             │
│ description (TEXT)              │
│ date_creation (DATETIME)        │
│ resolvue (BOOL)                 │
└─────────────────────────────────┘
```

---

## 🔌 API REST — Endpoints détaillés

### Gestion des années scolaires

| Méthode | Endpoint | Description | Réponse |
|---------|----------|-------------|---------|
| GET | `/api/annees` | Lister toutes les années | `{annees: [{id, annee, active}]}` |
| POST | `/api/annees` | Créer une année | `{id, annee, active}` |
| GET | `/api/annees/active` | Récupérer l'année active | `{id, annee, active}` |
| PUT | `/api/annees/:id/activate` | Activer une année | `{success, message}` |

### Gestion des classes

| Méthode | Endpoint | Description | Réponse |
|---------|----------|-------------|---------|
| GET | `/api/classes` | Classes de l'année active | `{classes: [{id, nom, niveau}]}` |
| POST | `/api/classes` | Créer une classe | `{id, nom, niveau}` |
| GET | `/api/classes/:id` | Détails d'une classe | `{id, nom, niveau, matieres}` |
| DELETE | `/api/classes/:id` | Supprimer une classe | `{success, message}` |

### Gestion des coefficients

| Méthode | Endpoint | Description | Réponse |
|---------|----------|-------------|---------|
| GET | `/api/coefficients/:classe_id` | Lister coefficients d'une classe | `{coefficients: [{matiere, coefficient}]}` |
| POST | `/api/coefficients` | Ajouter/modifier un coefficient | `{success, message}` |
| Body | - | `{classe_id, matiere, coefficient}` | - |

### Gestion des élèves

| Méthode | Endpoint | Description | Réponse |
|---------|----------|-------------|---------|
| GET | `/api/eleves/classe/:classe_id` | Lister élèves d'une classe | `{eleves: [{id, nom, prenom, matricule}]}` |
| POST | `/api/eleves/import` | Importer élèves (CSV) | `{success, count, errors}` |
| GET | `/api/eleves/:id` | Fiche complète d'un élève | `{id, nom, prenom, notes, courbes, alertes}` |
| DELETE | `/api/eleves/:id` | Supprimer un élève | `{success, message}` |

### Gestion des notes

| Méthode | Endpoint | Description | Réponse |
|---------|----------|-------------|---------|
| POST | `/api/notes/import/preview` | Prévisualiser import notes | `{preview: [], warnings: [], errors: []}` |
| POST | `/api/notes/import` | Importer notes (CSV) | `{success, count, alertes}` |
| POST | `/api/notes/manuel` | Ajouter note manuellement | `{id, success, alertes}` |
| PUT | `/api/notes/:id` | Modifier une note | `{success, message}` |
| DELETE | `/api/notes/:id` | Supprimer une note | `{success, message}` |

### Tableau de bord

| Méthode | Endpoint | Description | Réponse |
|---------|----------|-------------|---------|
| GET | `/api/dashboard/:classe_id` | Données tableau de bord classe | `{eleves_list, alertes, stats}` |
| GET | `/api/dashboard/eleve/:eleve_id` | Fiche détaillée élève | `{notes, courbes, tendances, alertes}` |
| GET | `/api/alertes` | Lister alertes non résolues | `{alertes: [{type, severite, description}]}` |

---

## 📊 Configuration des matières par niveau

L'application supporte plusieurs niveaux scolaires avec des matières et coefficients spécifiques :

### Collège (6ème à 3ème)
```
6ème, 5ème, 4ème, 3ème
Matières : Français, Mathématiques, Anglais, Espagnol, Histoire-Géographie,
           Éducation Civique, Physique-Chimie, SVT, EPS, Technologie,
           Arts Plastiques, Musique
```

### Lycée (2nde à Tle)
```
2nde : socle général
1ère A/C/D : filières + spécialités
Tle A/C/D : filières + option terminal
```

---

## 🖥️ Interface utilisateur

### Page unique (SPA - Single Page Application)

L'application utilise une interface HTML unique avec navigation par onglets.

#### Onglets principaux

1. **Configuration**
   - Créer/gérer années scolaires
   - Créer/gérer classes
   - Configurer les coefficients des matières
   - Importer la liste des élèves

2. **Tableau de bord**
   - Vue synthétique des classes
   - Indicateurs de performance (couleurs : vert/orange/rouge)
   - Alertes pédagogiques non résolues
   - État des imports par matière

3. **Import de notes**
   - Sélectionner classe et matière
   - Drag & drop ou sélection de fichier CSV
   - Prévisualisation avec rapport de cohérence
   - Confirmation et application des notes

4. **Gestion élèves**
   - Recherche et filtrage par classe
   - Voir fiche détaillée
   - Modifier/ajouter notes manuellement

5. **Rapports**
   - Statistiques par classe (moyenne, écart-type, distribution)
   - Comparaison inter-classes
   - Export en Excel (optionnel)

### Fiche élève détaillée

```
┌─────────────────────────────────────┐
│ Nom : KOUASSI Jean                  │
│ Classe : Terminale S                │
│ Moyenne générale : 14.5/20          │
├─────────────────────────────────────┤
│ Matière          │ Moyenne │ Trend  │
├──────────────────┼─────────┼────────┤
│ Français         │ 15/20   │ ↗ Prog │
│ Mathématiques    │ 16/20   │ → Stab │
│ Anglais          │ 12/20   │ ↘ Rég  │
├─────────────────────────────────────┤
│ [Courbes spline par matière]        │
│ [Graphique historique notes]        │
├─────────────────────────────────────┤
│ Alertes actives : 1                 │
│ ⚠️ Anglais : Baisse régulière       │
└─────────────────────────────────────┘
```

---

## 📥 Format des fichiers CSV

### Format : Liste d'élèves (import)
```csv
matricule,nom,prenom,date_naissance
2024-001,Kouassi,Jean,2007-03-15
2024-002,Traoré,Marie,2006-11-22
2024-003,Dubois,Paul,2007-01-10
```

**Règles de validation :**
- Matricule : unique par classe, non vide
- Nom/Prénom : non vides, max 50 caractères
- Date de naissance : format YYYY-MM-DD, pertinente (âge 8-25 ans)

### Format : Notes (import par professeur)
```csv
matricule,nom_eleve,note,date
2024-001,Kouassi Jean,14,2026-04-01
2024-002,Traoré Marie,10,2026-04-02
2024-003,Dubois Paul,18,2026-04-01
```

**Règles de validation :**
- Matricule : doit exister dans la classe
- Note : numérique entre 0 et 20 (1 décimale acceptable)
- Date : format YYYY-MM-DD, cohérente avec chronologie

**Rapport de cohérence généré :**
- ✅ Notes valides et importées
- ⚠️ Avertissements (note extrême, élève absent, doublon)
- ❌ Erreurs (matricule invalide, format incorrect)

---

## 🔍 Logique métier — Alertes et analyses

### Génération automatique d'alertes

L'application génère 4 types d'alertes basées sur les notes :

#### 1. Alerte "Baisse de performance"
**Déclenchement :**
- Moyenne mobile sur 5 dernières notes < moyenne antérieure - 2 points
- Deux notes consécutives < 10/20

**Sévérité :** 3/5

#### 2. Alerte "Excellence maintenue"
**Déclenchement :**
- Moyenne sur 5 dernières notes > 17/20

**Sévérité :** 1/5 (info, félicitations)

#### 3. Alerte "Difficulté persistante"
**Déclenchement :**
- Plus de 3 notes consécutives < 8/20

**Sévérité :** 5/5 (critique)

#### 4. Alerte "Progression encourageante"
**Déclenchement :**
- Moyenne mobile augmente de 2 points sur 5 notes

**Sévérité :** 2/5 (info positive)

### Calculs de tendances

**Courbe spline :**
- Interpolation lisse des points de notes
- Affichage sur graphique avec progression/régression
- Permet de visualiser la trajectoire long terme

**Indicateurs visuels :**
- 🟢 Vert : progression ou bon niveau (>14)
- 🟡 Orange : stabilité moyenne (10-14)
- 🔴 Rouge : difficulté ou régression (<10)

---

## 🚀 Flux d'utilisation complet

### Étape 1 : Configuration initiale
```
1. Administrateur accède à l'onglet Configuration
2. Crée l'année scolaire (ex: 2025-2026)
3. Crée les classes (ex: 6ème A, 5ème C, Terminale S)
4. Configure les coefficients pour chaque classe/matière
5. Importe la liste des élèves (CSV par classe)
   → Rapport : X élèves importés, Y erreurs
```

### Étape 2 : Import des notes
```
1. Professeur prépare son fichier CSV (matricule, nom, note, date)
2. Admin/directeur accède à onglet "Import de notes"
3. Sélectionne classe et matière
4. Drag & drop du CSV
5. Système génère prévisualisation avec :
   - ✅ 28 notes valides
   - ⚠️ 2 avertissements (note 19.5, élève absent)
   - ❌ 0 erreur
6. Admin clique "Confirmer l'import"
7. Système ajoute les notes à la BD et re-calcule les alertes
```

### Étape 3 : Suivi et analyse
```
1. Admin accède au Tableau de bord
   → Voit synthèse par classe avec indicateurs couleur
   → Voit liste des alertes critiques
2. Clique sur une classe pour voir liste d'élèves
3. Clique sur un élève pour voir fiche détaillée :
   - Notes par matière avec historique
   - Courbes spline (progression/régression)
   - Alertes actives spécifiques
   - Tendances (ex: "Baisse continue en Math")
4. Peut modifier ou ajouter des notes manuellement
5. Peut marquer une alerte comme "résolue"
```

---

## ⚙️ Instructions de développement complet

### Phase 1 : Préparation et structuration (1-2 heures)

**Tâches :**
1. Créer la structure du projet (dossiers, fichiers)
2. Initialiser Flask et configurer les routes
3. Créer la base de données SQLite avec schéma complet
4. Écrire les fonctions d'initialisation de la BD

**Fichiers à créer/modifier :**
- `app/app.py` : squelette + init_db()
- `app/static/css/style.css` : styles de base
- `app/templates/index.html` : structure HTML/onglets
- `app/static/js/app.js` : gestion des onglets

### Phase 2 : Backend - API REST (3-4 heures)

**Tâches :**
1. Implémenter endpoints années scolaires (CRUD)
2. Implémenter endpoints classes (CRUD)
3. Implémenter endpoints coefficients (GET/POST)
4. Implémenter endpoints élèves (GET, import CSV, CRUD)
5. Implémenter endpoints notes (import preview, import, manuel, PUT, DELETE)
6. Implémenter endpoints alertes

**Fichiers à modifier :**
- `app/app.py` : ajouter toutes les routes

### Phase 3 : Logique métier et validation (2-3 heures)

**Tâches :**
1. Créer validateurs CSV (élèves, notes)
2. Créer générateurs de rapports (preview import)
3. Implémenter logique d'alerte automatique
4. Implémenter calcul de tendances
5. Implémenter interpolation spline (scipy)

**Fichiers à créer/modifier :**
- `app/app.py` : ajouter fonctions de validation et calcul
- Optionnel : `app/utils.py` : extraire logique métier

### Phase 4 : Frontend - Interface utilisateur (3-4 heures)

**Tâches :**
1. Implémenter onglet Configuration (formulaires, importation)
2. Implémenter onglet Tableau de bord (affichage données, couleurs)
3. Implémenter onglet Import de notes (preview, validation)
4. Implémenter onglet Gestion élèves (recherche, fiche détaillée)
5. Intégrer graphiques (Chart.js ou Plotly)

**Fichiers à modifier :**
- `app/templates/index.html` : HTML pour tous les onglets
- `app/static/js/app.js` : logique JavaScript, appels API
- `app/static/css/style.css` : mise en forme

### Phase 5 : Intégration et tests (2-3 heures)

**Tâches :**
1. Tester chaque endpoint API individuellement
2. Tester flux complet : création année → classe → import élèves → import notes
3. Tester gestion d'erreurs et validation
4. Tester alertes avec données de test
5. Tester graphiques et courbes spline
6. Optimiser performances (si besoin)

**Fichiers de test :**
- Utiliser fichiers CSV existants : `notes_6eme_mathematiques.csv`, `test_eleves.csv`
- Utiliser utilitaire : `randomize_notes.py` pour générer données de test

---

## 📦 Dépendances Python

```
Flask==2.3.0
pandas==2.0.0
scipy==1.10.0
numpy==1.24.0
```

**Installation :**
```bash
pip install -r requirements.txt
```

---

## 🎨 Directives de design

### Palette de couleurs
- **Primaire (Bleu)** : #1e3a8a (en-têtes, boutons principaux)
- **Succès (Vert)** : #16a34a (bonnes performances, ✅)
- **Attention (Orange)** : #ea580c (avertissements, tendances)
- **Danger (Rouge)** : #dc2626 (critiques, ❌)
- **Neutre (Gris)** : #6b7280 (textes secondaires)

### Typographie
- Police : System default ou "Segoe UI", Arial, sans-serif
- Taille de base : 14px
- Titres h1 : 28px / h2 : 22px / h3 : 18px

### Responsivité
- Desktop : 1920px+
- Tablet : 768px - 1024px
- Mobile : 320px - 767px

### Accessibilité
- Tous les boutons doivent avoir un `:hover` visible
- Contraste minimum WCAG AA (4.5:1 pour texte)
- Support clavier (Tab, Enter, Escape)

---

## 📈 Améliorations futures

1. **Authentication & Permissions** : Rôles (Admin, Directeur, Prof, Parent)
2. **Export Excel** : Générer rapports d'établissement
3. **Notifications** : Alertes email pour parents/profs
4. **Multilangue** : Français/Anglais
5. **Graphiques avancés** : Comparaison inter-classes, heatmaps
6. **API Python** : Module `gestenote` pour scripts externes
7. **Mobile app** : React Native ou Flutter
8. **Synchronisation** : Avec logiciels externes (Pronote, Managebac)

---

## 📞 Support et maintenance

**Fichiers critiques à sauvegarder :**
- `app/scolaire.db` : base de données (BACKUP RÉGULIER!)
- `app/app.py` : code métier
- `app/static/` et `app/templates/` : interface

**Problèmes courants :**
- Port 5000 déjà utilisé → Changer `app.run(port=5001)`
- Erreur de permissions BD → Vérifier droits d'accès sur le dossier `/app`
- CSV non reconnu → Vérifier encodage (UTF-8) et séparateur (virgule)

---

## ✅ Checklist de développement

- [ ] Phase 1 complétée : Structure et init BD
- [ ] Phase 2 complétée : Tous endpoints API testés
- [ ] Phase 3 complétée : Validation et alertes fonctionnels
- [ ] Phase 4 complétée : Interface utilisateur complète
- [ ] Phase 5 complétée : Tests intégration réussis
- [ ] Documentation mise à jour
- [ ] Base de données backupée
- [ ] Prêt pour déploiement

---

**Version** : 2.0  
**Dernière mise à jour** : 11 mai 2026  
**État** : En cours de développement
