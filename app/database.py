import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scolaire.db')

MATIERES_PAR_NIVEAU = {
    '6eme': [
        ('Français', 5), ('Mathématiques', 5), ('Anglais', 3), ('Espagnol', 2),
        ('Histoire-Géographie', 3), ('Éducation Civique', 1), ('Physique-Chimie', 3),
        ('SVT', 3), ('EPS', 1), ('Technologie', 2), ('Arts Plastiques', 1), ('Musique', 1),
    ],
    '5eme': [
        ('Français', 5), ('Mathématiques', 5), ('Anglais', 3), ('Espagnol', 2),
        ('Histoire-Géographie', 3), ('Éducation Civique', 1), ('Physique-Chimie', 3),
        ('SVT', 3), ('EPS', 1), ('Technologie', 2), ('Arts Plastiques', 1), ('Musique', 1),
    ],
    '4eme': [
        ('Français', 5), ('Mathématiques', 5), ('Anglais', 3), ('Espagnol', 2),
        ('Histoire-Géographie', 3), ('Éducation Civique', 1), ('Physique-Chimie', 3),
        ('SVT', 3), ('EPS', 1), ('Technologie', 2), ('Arts Plastiques', 1), ('Musique', 1),
    ],
    '3eme': [
        ('Français', 5), ('Mathématiques', 5), ('Anglais', 3), ('Espagnol', 2),
        ('Histoire-Géographie', 3), ('Éducation Civique', 1), ('Physique-Chimie', 3),
        ('SVT', 3), ('EPS', 1), ('Technologie', 2), ('Arts Plastiques', 1), ('Musique', 1),
    ],
    '2nde': [
        ('Français', 4), ('Mathématiques', 5), ('Anglais', 3), ('Espagnol', 2),
        ('Histoire-Géographie', 3), ('Physique-Chimie', 4), ('SVT', 3),
        ('EPS', 1), ('SES', 2), ('SNT', 1),
    ],
    '1ere_A': [
        ('Français', 3), ('Mathématiques', 4), ('Anglais', 3), ('Espagnol', 2),
        ('Histoire-Géographie', 3), ('Philosophie', 2), ('EPS', 1),
        ('Littérature', 5), ('SES', 3),
    ],
    '1ere_C': [
        ('Français', 3), ('Mathématiques', 6), ('Anglais', 3), ('Espagnol', 2),
        ('Histoire-Géographie', 3), ('Philosophie', 2), ('EPS', 1),
        ('Physique-Chimie', 5), ('SVT', 4),
    ],
    '1ere_D': [
        ('Français', 3), ('Mathématiques', 5), ('Anglais', 3), ('Espagnol', 2),
        ('Histoire-Géographie', 3), ('Philosophie', 2), ('EPS', 1),
        ('Physique-Chimie', 4), ('SVT', 5),
    ],
    'Tle_A': [
        ('Mathématiques', 4), ('Anglais', 3), ('Espagnol', 2),
        ('Histoire-Géographie', 3), ('Philosophie', 3), ('EPS', 1),
        ('Littérature', 6), ('SES', 4),
    ],
    'Tle_C': [
        ('Mathématiques', 7), ('Anglais', 3), ('Espagnol', 2),
        ('Histoire-Géographie', 3), ('Philosophie', 3), ('EPS', 1),
        ('Physique-Chimie', 6), ('SVT', 4),
    ],
    'Tle_D': [
        ('Mathématiques', 5), ('Anglais', 3), ('Espagnol', 2),
        ('Histoire-Géographie', 3), ('Philosophie', 3), ('EPS', 1),
        ('Physique-Chimie', 5), ('SVT', 6),
    ],
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS AnneesScolaires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            annee VARCHAR(9) NOT NULL UNIQUE,
            active INTEGER NOT NULL DEFAULT 0,
            date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS Classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            annee_id INTEGER NOT NULL,
            nom VARCHAR(50) NOT NULL,
            niveau VARCHAR(20) NOT NULL,
            date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (annee_id) REFERENCES AnneesScolaires(id) ON DELETE CASCADE,
            UNIQUE(annee_id, nom)
        );

        CREATE TABLE IF NOT EXISTS Eleves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            classe_id INTEGER NOT NULL,
            matricule VARCHAR(20) NOT NULL,
            nom VARCHAR(50) NOT NULL,
            prenom VARCHAR(50) NOT NULL,
            date_naissance DATE,
            date_import DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (classe_id) REFERENCES Classes(id) ON DELETE CASCADE,
            UNIQUE(classe_id, matricule)
        );

        CREATE TABLE IF NOT EXISTS Matieres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            classe_id INTEGER NOT NULL,
            nom VARCHAR(100) NOT NULL,
            coefficient INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (classe_id) REFERENCES Classes(id) ON DELETE CASCADE,
            UNIQUE(classe_id, nom)
        );

        CREATE TABLE IF NOT EXISTS Notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eleve_id INTEGER NOT NULL,
            matiere_id INTEGER NOT NULL,
            note REAL NOT NULL CHECK(note >= 0 AND note <= 20),
            date_note DATE NOT NULL,
            source VARCHAR(20) NOT NULL DEFAULT 'import',
            date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (eleve_id) REFERENCES Eleves(id) ON DELETE CASCADE,
            FOREIGN KEY (matiere_id) REFERENCES Matieres(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Alertes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eleve_id INTEGER NOT NULL,
            matiere_id INTEGER,
            type_alerte VARCHAR(50) NOT NULL,
            severite INTEGER NOT NULL CHECK(severite >= 1 AND severite <= 5),
            description TEXT NOT NULL,
            date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            resolvue INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (eleve_id) REFERENCES Eleves(id) ON DELETE CASCADE,
            FOREIGN KEY (matiere_id) REFERENCES Matieres(id) ON DELETE SET NULL
        );
    ''')

    conn.commit()
    conn.close()