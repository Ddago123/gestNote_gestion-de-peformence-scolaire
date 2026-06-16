import math
from app.database import get_db, MATIERES_PAR_NIVEAU


# ─── AnneesScolaires ───────────────────────────────────────────────

def annee_get_all():
    db = get_db()
    rows = db.execute('SELECT * FROM AnneesScolaires ORDER BY annee DESC').fetchall()
    db.close()
    return [dict(r) for r in rows]


def annee_get_active():
    db = get_db()
    row = db.execute('SELECT * FROM AnneesScolaires WHERE active = 1').fetchone()
    db.close()
    return dict(row) if row else None


def annee_create(annee):
    db = get_db()
    try:
        cur = db.execute('INSERT INTO AnneesScolaires (annee, active) VALUES (?, 0)', (annee,))
        db.commit()
        annee_id = cur.lastrowid
        db.close()
        return annee_id, None
    except Exception as e:
        db.close()
        return None, str(e)


def annee_activate(annee_id):
    db = get_db()
    db.execute('UPDATE AnneesScolaires SET active = 0')
    db.execute('UPDATE AnneesScolaires SET active = 1 WHERE id = ?', (annee_id,))
    db.commit()
    db.close()


# ─── Classes ───────────────────────────────────────────────────────

def classe_get_by_annee(annee_id):
    db = get_db()
    rows = db.execute(
        'SELECT c.*, COUNT(e.id) as nb_eleves '
        'FROM Classes c LEFT JOIN Eleves e ON e.classe_id = c.id '
        'WHERE c.annee_id = ? GROUP BY c.id ORDER BY c.nom',
        (annee_id,)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def classe_get_by_id(classe_id):
    db = get_db()
    row = db.execute('SELECT * FROM Classes WHERE id = ?', (classe_id,)).fetchone()
    db.close()
    return dict(row) if row else None


def classe_create(annee_id, nom, niveau):
    db = get_db()
    try:
        cur = db.execute(
            'INSERT INTO Classes (annee_id, nom, niveau) VALUES (?, ?, ?)',
            (annee_id, nom, niveau)
        )
        classe_id = cur.lastrowid
        _insert_matieres_par_defaut(db, classe_id, niveau)
        db.commit()
        db.close()
        return classe_id, None
    except Exception as e:
        db.close()
        return None, str(e)


def classe_delete(classe_id):
    db = get_db()
    db.execute('DELETE FROM Classes WHERE id = ?', (classe_id,))
    db.commit()
    db.close()


# ─── Matières / Coefficients ──────────────────────────────────────

def _insert_matieres_par_defaut(db, classe_id, niveau):
    matieres = MATIERES_PAR_NIVEAU.get(niveau, [])
    for nom, coef in matieres:
        db.execute(
            'INSERT OR IGNORE INTO Matieres (classe_id, nom, coefficient) VALUES (?, ?, ?)',
            (classe_id, nom, coef)
        )


def matieres_get_by_classe(classe_id):
    db = get_db()
    rows = db.execute(
        'SELECT * FROM Matieres WHERE classe_id = ? ORDER BY nom', (classe_id,)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def coefficient_upsert(classe_id, matiere, coefficient):
    db = get_db()
    try:
        db.execute(
            'INSERT INTO Matieres (classe_id, nom, coefficient) VALUES (?, ?, ?) '
            'ON CONFLICT(classe_id, nom) DO UPDATE SET coefficient = excluded.coefficient',
            (classe_id, matiere, coefficient)
        )
        db.commit()
        db.close()
        return True, None
    except Exception as e:
        db.close()
        return False, str(e)


# ─── Élèves ───────────────────────────────────────────────────────

def eleve_get_by_classe(classe_id):
    db = get_db()
    rows = db.execute(
        'SELECT * FROM Eleves WHERE classe_id = ? ORDER BY nom, prenom', (classe_id,)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def eleve_get_by_id(eleve_id):
    db = get_db()
    row = db.execute(
        'SELECT e.*, c.nom as classe_nom, c.niveau as classe_niveau '
        'FROM Eleves e JOIN Classes c ON c.id = e.classe_id WHERE e.id = ?',
        (eleve_id,)
    ).fetchone()
    db.close()
    return dict(row) if row else None


def eleve_get_by_matricule(classe_id, matricule):
    db = get_db()
    row = db.execute(
        'SELECT * FROM Eleves WHERE classe_id = ? AND matricule = ?',
        (classe_id, matricule)
    ).fetchone()
    db.close()
    return dict(row) if row else None


def eleve_create(classe_id, matricule, nom, prenom, date_naissance):
    db = get_db()
    try:
        cur = db.execute(
            'INSERT INTO Eleves (classe_id, matricule, nom, prenom, date_naissance) '
            'VALUES (?, ?, ?, ?, ?)',
            (classe_id, matricule, nom, prenom, date_naissance)
        )
        db.commit()
        eleve_id = cur.lastrowid
        db.close()
        return eleve_id, None
    except Exception as e:
        db.close()
        return None, str(e)


def eleve_import_bulk(classe_id, eleves_data):
    """eleves_data: list of (matricule, nom, prenom, date_naissance)"""
    db = get_db()
    created = 0
    errors = []
    for i, (matricule, nom, prenom, date_naissance) in enumerate(eleves_data):
        try:
            db.execute(
                'INSERT INTO Eleves (classe_id, matricule, nom, prenom, date_naissance) '
                'VALUES (?, ?, ?, ?, ?)',
                (classe_id, matricule, nom, prenom, date_naissance)
            )
            created += 1
        except Exception as e:
            errors.append({'ligne': i + 2, 'matricule': matricule, 'erreur': str(e)})
    db.commit()
    db.close()
    return created, errors


def eleve_delete(eleve_id):
    db = get_db()
    db.execute('DELETE FROM Eleves WHERE id = ?', (eleve_id,))
    db.commit()
    db.close()


def eleve_search(annee_id, query):
    db = get_db()
    rows = db.execute(
        'SELECT e.*, c.nom as classe_nom FROM Eleves e '
        'JOIN Classes c ON c.id = e.classe_id '
        'WHERE c.annee_id = ? AND (e.nom LIKE ? OR e.prenom LIKE ? OR e.matricule LIKE ?) '
        'ORDER BY e.nom LIMIT 50',
        (annee_id, f'%{query}%', f'%{query}%', f'%{query}%')
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


# ─── Notes ─────────────────────────────────────────────────────────

def note_get_by_eleve_matiere(eleve_id, matiere_id=None):
    db = get_db()
    if matiere_id:
        rows = db.execute(
            'SELECT n.*, m.nom as matiere_nom FROM Notes n '
            'JOIN Matieres m ON m.id = n.matiere_id '
            'WHERE n.eleve_id = ? AND n.matiere_id = ? ORDER BY n.date_note',
            (eleve_id, matiere_id)
        ).fetchall()
    else:
        rows = db.execute(
            'SELECT n.*, m.nom as matiere_nom FROM Notes n '
            'JOIN Matieres m ON m.id = n.matiere_id '
            'WHERE n.eleve_id = ? ORDER BY m.nom, n.date_note',
            (eleve_id,)
        ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def note_create(eleve_id, matiere_id, note, date_note, source='manuel'):
    db = get_db()
    cur = db.execute(
        'INSERT INTO Notes (eleve_id, matiere_id, note, date_note, source) VALUES (?, ?, ?, ?, ?)',
        (eleve_id, matiere_id, note, date_note, source)
    )
    db.commit()
    note_id = cur.lastrowid
    db.close()
    return note_id


def note_update(note_id, note, date_note):
    db = get_db()
    db.execute(
        'UPDATE Notes SET note = ?, date_note = ? WHERE id = ?',
        (note, date_note, note_id)
    )
    db.commit()
    db.close()


def note_delete(note_id):
    db = get_db()
    db.execute('DELETE FROM Notes WHERE id = ?', (note_id,))
    db.commit()
    db.close()


def note_import_bulk(notes_data):
    """notes_data: list of (eleve_id, matiere_id, note, date_note)"""
    db = get_db()
    created = 0
    for eleve_id, matiere_id, note, date_note in notes_data:
        db.execute(
            'INSERT INTO Notes (eleve_id, matiere_id, note, date_note, source) VALUES (?, ?, ?, ?, ?)',
            (eleve_id, matiere_id, note, date_note, 'import')
        )
        created += 1
    db.commit()
    db.close()
    return created


def note_get_stats_by_classe_matiere(classe_id):
    db = get_db()
    rows = db.execute(
        'SELECT m.nom as matiere, m.coefficient, n.note '
        'FROM Notes n '
        'JOIN Eleves e ON e.id = n.eleve_id '
        'JOIN Matieres m ON m.id = n.matiere_id '
        'WHERE e.classe_id = ? ORDER BY m.nom',
        (classe_id,)
    ).fetchall()
    db.close()

    matieres = {}
    for row in rows:
        nom = row['matiere']
        if nom not in matieres:
            matieres[nom] = {'matiere': nom, 'coefficient': row['coefficient'], 'notes': []}
        matieres[nom]['notes'].append(row['note'])

    result = []
    for nom, data in matieres.items():
        notes = data['notes']
        n = len(notes)
        moyenne = sum(notes) / n
        if n >= 2:
            variance = sum((x - moyenne) ** 2 for x in notes) / (n - 1)
            ecart_type = round(math.sqrt(variance), 2)
        else:
            ecart_type = 0.0
        result.append({
            'matiere': nom,
            'coefficient': data['coefficient'],
            'moyenne': round(moyenne, 2),
            'nb_notes': n,
            'min': min(notes),
            'max': max(notes),
            'ecart_type': ecart_type,
        })

    return sorted(result, key=lambda x: x['matiere'])


def note_get_existing_keys(matiere_id):
    """Retourne un set de (eleve_id, date_note) déjà présents pour cette matière."""
    db = get_db()
    rows = db.execute(
        'SELECT eleve_id, date_note FROM Notes WHERE matiere_id = ?',
        (matiere_id,)
    ).fetchall()
    db.close()
    return {(row['eleve_id'], row['date_note']) for row in rows}


def note_get_all_by_classe(classe_id):
    db = get_db()
    rows = db.execute(
        'SELECT n.*, m.nom as matiere_nom FROM Notes n '
        'JOIN Eleves e ON e.id = n.eleve_id '
        'JOIN Matieres m ON m.id = n.matiere_id '
        'WHERE e.classe_id = ? ORDER BY n.eleve_id, m.nom, n.date_note',
        (classe_id,)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def alerte_count_by_eleve_classe(classe_id):
    db = get_db()
    rows = db.execute(
        'SELECT a.eleve_id, COUNT(*) as nb '
        'FROM Alertes a '
        'JOIN Eleves e ON e.id = a.eleve_id '
        'WHERE e.classe_id = ? AND a.resolvue = 0 '
        'GROUP BY a.eleve_id',
        (classe_id,)
    ).fetchall()
    db.close()
    return {row['eleve_id']: row['nb'] for row in rows}


# ─── Alertes ───────────────────────────────────────────────────────

def alerte_get_all_active(annee_id=None):
    db = get_db()
    if annee_id:
        rows = db.execute(
            'SELECT a.*, e.nom as eleve_nom, e.prenom as eleve_prenom, '
            'c.id as classe_id, c.nom as classe_nom, m.nom as matiere_nom '
            'FROM Alertes a '
            'JOIN Eleves e ON e.id = a.eleve_id '
            'JOIN Classes c ON c.id = e.classe_id '
            'LEFT JOIN Matieres m ON m.id = a.matiere_id '
            'WHERE a.resolvue = 0 AND c.annee_id = ? '
            'ORDER BY a.severite DESC, a.date_creation DESC',
            (annee_id,)
        ).fetchall()
    else:
        rows = db.execute(
            'SELECT a.*, e.nom as eleve_nom, e.prenom as eleve_prenom, '
            'c.id as classe_id, c.nom as classe_nom, m.nom as matiere_nom '
            'FROM Alertes a '
            'JOIN Eleves e ON e.id = a.eleve_id '
            'JOIN Classes c ON c.id = e.classe_id '
            'LEFT JOIN Matieres m ON m.id = a.matiere_id '
            'WHERE a.resolvue = 0 '
            'ORDER BY a.severite DESC, a.date_creation DESC'
        ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def alerte_get_by_eleve(eleve_id):
    db = get_db()
    rows = db.execute(
        'SELECT a.*, m.nom as matiere_nom FROM Alertes a '
        'LEFT JOIN Matieres m ON m.id = a.matiere_id '
        'WHERE a.eleve_id = ? AND a.resolvue = 0 '
        'ORDER BY a.severite DESC',
        (eleve_id,)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def alerte_create(eleve_id, type_alerte, severite, description, matiere_id=None):
    db = get_db()
    existing = db.execute(
        'SELECT id FROM Alertes WHERE eleve_id = ? AND type_alerte = ? '
        'AND (matiere_id = ? OR (matiere_id IS NULL AND ? IS NULL)) AND resolvue = 0',
        (eleve_id, type_alerte, matiere_id, matiere_id)
    ).fetchone()
    if existing:
        db.close()
        return None
    cur = db.execute(
        'INSERT INTO Alertes (eleve_id, matiere_id, type_alerte, severite, description) '
        'VALUES (?, ?, ?, ?, ?)',
        (eleve_id, matiere_id, type_alerte, severite, description)
    )
    db.commit()
    alerte_id = cur.lastrowid
    db.close()
    return alerte_id


def alerte_resolve(alerte_id):
    db = get_db()
    db.execute('UPDATE Alertes SET resolvue = 1 WHERE id = ?', (alerte_id,))
    db.commit()
    db.close()


def alerte_resolve_all_by_classe(classe_id):
    db = get_db()
    db.execute(
        'UPDATE Alertes SET resolvue = 1 '
        'WHERE resolvue = 0 AND eleve_id IN (SELECT id FROM Eleves WHERE classe_id = ?)',
        (classe_id,)
    )
    db.commit()
    db.close()


def alerte_resolve_all_eleve(eleve_id):
    db = get_db()
    db.execute('UPDATE Alertes SET resolvue = 1 WHERE eleve_id = ?', (eleve_id,))
    db.commit()
    db.close()