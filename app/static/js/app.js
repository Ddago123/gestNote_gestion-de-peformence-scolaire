/* ═══════════════════════════════════════════
   GestNote — Frontend JavaScript
   ═══════════════════════════════════════════ */

let distributionChart = null;
let currentDashboardClasseId = null;
let rapportData = null;

/* ─── Toast notifications ─── */
let _toastEl;
function showToast(text, type = 'info', duration = 3500) {
    if (!_toastEl) {
        _toastEl = document.createElement('div');
        _toastEl.className = 'toast-container';
        document.body.appendChild(_toastEl);
    }
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.textContent = text;
    _toastEl.appendChild(t);
    setTimeout(() => {
        t.classList.add('toast-out');
        t.addEventListener('animationend', () => t.remove(), { once: true });
    }, duration);
}

/* ─── Button loading state ─── */
function setLoading(btn, loading) {
    if (!btn) return;
    if (loading) {
        btn.dataset.origHtml = btn.innerHTML;
        btn.innerHTML = '<span class="spinner"></span>';
        btn.disabled = true;
    } else {
        btn.innerHTML = btn.dataset.origHtml ?? btn.innerHTML;
        btn.disabled = false;
    }
}

/* ─── Content loading placeholder ─── */
function loadingHtml(text = 'Chargement...') {
    return `<div class="loading-placeholder"><span class="spinner"></span>${text}</div>`;
}

function escapeHtml(v) {
    return String(v ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initKeyboardShortcuts();
    checkAuthAndInit();
});

function initKeyboardShortcuts() {
    document.getElementById('inputAnnee').addEventListener('keydown', e => { if (e.key === 'Enter') creerAnnee(); });
    document.getElementById('inputClasseNom').addEventListener('keydown', e => { if (e.key === 'Enter') creerClasse(); });
    document.getElementById('loginUser').addEventListener('keydown', e => { if (e.key === 'Enter') login(); });
    document.getElementById('loginPass').addEventListener('keydown', e => { if (e.key === 'Enter') login(); });
}

async function checkAuthAndInit() {
    try {
        const data = await fetch('/api/auth/status').then(r => r.json());
        if (data.authenticated) {
            initApp();
        } else {
            showLoginOverlay();
        }
    } catch {
        showLoginOverlay();
    }
}

function initApp() {
    chargerAnnees();
    chargerClassesDansSelects();
    initDateInput();
}

/* ─── Auth ─── */
function showLoginOverlay() {
    document.getElementById('loginOverlay').style.display = 'flex';
    document.getElementById('loginUser').focus();
}

function hideLoginOverlay() {
    document.getElementById('loginOverlay').style.display = 'none';
}

async function login() {
    const username = document.getElementById('loginUser').value.trim();
    const password = document.getElementById('loginPass').value;
    const btn = document.getElementById('btnLogin');
    const errEl = document.getElementById('loginError');
    if (!username || !password) return msg(errEl, 'Identifiant et mot de passe requis', 'error');
    setLoading(btn, true);
    try {
        await api('POST', '/api/auth/login', { username, password });
        hideLoginOverlay();
        initApp();
    } catch (e) {
        msg(errEl, e.message || 'Identifiants incorrects', 'error');
    } finally {
        setLoading(btn, false);
    }
}

async function logout() {
    try {
        await api('POST', '/api/auth/logout');
    } finally {
        showLoginOverlay();
    }
}

/* ─── Navigation par onglets ─── */
function initNavigation() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('tab-' + btn.dataset.tab).classList.add('active');

            if (btn.dataset.tab === 'dashboard') chargerDashboard();
            if (btn.dataset.tab === 'rapports') chargerRapports();
        });
    });
}

function initDateInput() {
    const d = new Date();
    document.getElementById('inputManuelDate').value = d.toISOString().split('T')[0];
}

/* ════════════════════════════════════════════
   API HELPER
   ════════════════════════════════════════════ */
async function api(method, url, body) {
    const opts = { method, headers: {} };
    if (body instanceof FormData) {
        opts.body = body;
    } else if (body) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(body);
    }
    const res = await fetch(url, opts);
    if (res.status === 401 && !url.includes('/api/auth/')) {
        showLoginOverlay();
        throw new Error('Session expirée, veuillez vous reconnecter');
    }
    const data = await res.json();
    if (!res.ok && data.error) throw new Error(data.error);
    return data;
}

function msg(el, text, type) {
    el.innerHTML = text ? `<span class="msg-${type || 'info'}">${text}</span>` : '';
}

/* ════════════════════════════════════════════
   ANNÉES
   ════════════════════════════════════════════ */
async function chargerAnnees() {
    try {
        const data = await api('GET', '/api/annees');
        const container = document.getElementById('listeAnnees');
        container.innerHTML = data.annees.map(a => `
            <div class="item-row">
                <span>${a.annee} ${a.active ? '<span class="badge badge-success">Active</span>' : ''}</span>
                ${!a.active ? `<button class="btn btn-sm btn-primary" onclick="activerAnnee(${a.id})">Activer</button>` : ''}
            </div>
        `).join('');
        majAnneeActive();
    } catch (e) { console.error(e); }
}

async function creerAnnee() {
    const input = document.getElementById('inputAnnee');
    const btn = document.getElementById('btnCreerAnnee');
    const val = input.value.trim();
    if (!val) return showToast('Veuillez saisir une année', 'warning');
    setLoading(btn, true);
    try {
        await api('POST', '/api/annees', { annee: val });
        input.value = '';
        chargerAnnees();
    } catch (e) { showToast(e.message, 'error'); }
    finally { setLoading(btn, false); }
}

async function activerAnnee(id) {
    await api('PUT', `/api/annees/${id}/activate`);
    chargerAnnees();
}

async function majAnneeActive() {
    try {
        const data = await api('GET', '/api/annees/active');
        document.getElementById('anneeActive').textContent = `Année : ${data.annee}`;
        chargerClassesDansSelects();
    } catch {
        document.getElementById('anneeActive').textContent = 'Aucune année active';
    }
}

/* ════════════════════════════════════════════
   CLASSES
   ════════════════════════════════════════════ */
async function chargerClasses(idListe, idSelect, idSelect2) {
    try {
        const data = await api('GET', '/api/classes');
        if (idListe) {
            const container = document.getElementById(idListe);
            container.innerHTML = data.classes.map(c => `
                <div class="item-row">
                    <span>${c.nom} <span class="badge badge-info">${c.niveau}</span> (${c.nb_eleves} élèves)</span>
                    <div>
                        <button class="btn btn-sm btn-primary" onclick="chargerFicheClasse(${c.id})">Détails</button>
                        <button class="btn btn-sm btn-danger" onclick="supprimerClasse(${c.id})">Suppr.</button>
                    </div>
                </div>
            `).join('');
        }
        const opts = '<option value="">Choisir une classe...</option>' +
            data.classes.map(c => `<option value="${c.id}">${c.nom}</option>`).join('');
        if (idSelect) document.getElementById(idSelect).innerHTML = opts;
        if (idSelect2) document.getElementById(idSelect2).innerHTML = opts;
        return data.classes;
    } catch { return []; }
}

async function chargerClassesDansSelects() {
    const classes = await chargerClasses(
        'listeClasses', 'inputCoefClasse', 'inputImportEleveClasse'
    );
    ['inputDashClasse', 'inputImportClasse', 'inputManuelClasse',
     'inputRapportClasse', 'inputBrowseClasse', 'inputAjoutClasse'].forEach(id => {
        const sel = document.getElementById(id);
        if (sel) {
            const current = sel.value;
            sel.innerHTML = '<option value="">Choisir une classe...</option>' +
                classes.map(c => `<option value="${c.id}">${c.nom}</option>`).join('');
            sel.value = current;
        }
    });
}

async function creerClasse() {
    const nom = document.getElementById('inputClasseNom').value.trim();
    const niveau = document.getElementById('inputClasseNiveau').value;
    const btn = document.getElementById('btnCreerClasse');
    if (!nom || !niveau) return showToast('Nom et niveau requis', 'warning');
    setLoading(btn, true);
    try {
        await api('POST', '/api/classes', { nom, niveau });
        document.getElementById('inputClasseNom').value = '';
        document.getElementById('inputClasseNiveau').value = '';
        chargerClassesDansSelects();
    } catch (e) { showToast(e.message, 'error'); }
    finally { setLoading(btn, false); }
}

async function supprimerClasse(id) {
    if (!confirm('Supprimer cette classe ?')) return;
    await api('DELETE', `/api/classes/${id}`);
    chargerClassesDansSelects();
}

async function chargerFicheClasse(id) {
    const detail = document.getElementById('detailClasse');
    if (detail.dataset.classeId == id && detail.style.display !== 'none') {
        detail.style.display = 'none';
        return;
    }
    detail.style.display = 'block';
    detail.innerHTML = '<p style="color:var(--gray-400)">Chargement...</p>';
    try {
        const data = await api('GET', `/api/classes/${id}`);
        detail.dataset.classeId = id;
        const matieres = data.matieres || [];
        detail.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                <strong>${data.nom}</strong>
                <span class="badge badge-info">${data.niveau} — ${matieres.length} matière(s)</span>
            </div>
            <div class="table-responsive">
                <table>
                    <thead><tr><th>Matière</th><th>Coefficient</th></tr></thead>
                    <tbody>${matieres.map(m => `<tr><td>${m.nom}</td><td>${m.coefficient}</td></tr>`).join('')}</tbody>
                </table>
            </div>
        `;
    } catch (e) {
        detail.innerHTML = `<span class="msg-error">Erreur: ${e.message}</span>`;
    }
}

/* ════════════════════════════════════════════
   COEFFICIENTS
   ════════════════════════════════════════════ */
async function chargerCoefficients() {
    const classeId = document.getElementById('inputCoefClasse').value;
    const container = document.getElementById('listeCoefficients');
    if (!classeId) { container.innerHTML = ''; return; }
    try {
        const data = await api('GET', `/api/coefficients/${classeId}`);
        container.innerHTML = data.coefficients.map(m => `
            <div class="item-row">
                <span>${escapeHtml(m.matiere)}</span>
                <div style="display:flex;align-items:center;gap:6px">
                    <input type="number" id="coef-${m.matiere}" value="${m.coefficient}"
                           min="1" max="10" style="width:60px;padding:4px 8px;border:1px solid var(--gray-300);border-radius:4px">
                    <button class="btn btn-sm btn-primary" onclick="sauverCoefficient('${m.matiere}', ${classeId}, this)">OK</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<p class="msg-error" style="padding:8px">Erreur de chargement des coefficients</p>';
    }
}

async function sauverCoefficient(matiere, classeId, btn) {
    const coef = parseInt(document.getElementById(`coef-${matiere}`).value);
    if (coef < 1 || coef > 10) return showToast('Coefficient entre 1 et 10', 'warning');
    setLoading(btn, true);
    try {
        await api('POST', '/api/coefficients', { classe_id: classeId, matiere, coefficient: coef });
        btn.disabled = false;
        btn.innerHTML = '✓';
        btn.classList.replace('btn-primary', 'btn-success');
        setTimeout(() => {
            btn.innerHTML = 'OK';
            btn.classList.replace('btn-success', 'btn-primary');
        }, 1500);
    } catch (e) {
        setLoading(btn, false);
        showToast(e.message, 'error');
    }
}

/* ════════════════════════════════════════════
   IMPORT ÉLÈVES
   ════════════════════════════════════════════ */
async function importEleves() {
    const classeId = document.getElementById('inputImportEleveClasse').value;
    const fileInput = document.getElementById('inputFichierEleves');
    const btn = document.getElementById('btnImportEleves');
    if (!classeId || !fileInput.files.length) return showToast('Sélectionnez une classe et un fichier', 'warning');

    const form = new FormData();
    form.append('file', fileInput.files[0]);
    form.append('classe_id', classeId);

    const el = document.getElementById('resultatImportEleves');
    el.innerHTML = '<span class="msg-info">Import en cours...</span>';
    setLoading(btn, true);

    try {
        const data = await api('POST', '/api/eleves/import', form);
        if (!data.success) {
            let html = `<span class="msg-error">${data.errors.length} erreur(s) lors de l'import :</span><ul>`;
            data.errors.forEach(err => {
                html += `<li>Ligne ${err.ligne}${err.matricule ? ` (${err.matricule})` : ''} : ${err.erreur}</li>`;
            });
            html += '</ul>';
            el.innerHTML = html;
        } else {
            msg(el, `${data.count} élèves importés avec succès`, 'success');
            showToast(`${data.count} élèves importés`, 'success');
            fileInput.value = '';
            chargerClassesDansSelects();
        }
    } catch (e) {
        msg(el, `Erreur: ${e.message}`, 'error');
    } finally {
        setLoading(btn, false);
    }
}

/* ════════════════════════════════════════════
   DASHBOARD
   ════════════════════════════════════════════ */
async function chargerDashboard() {
    const classeId = document.getElementById('inputDashClasse').value;
    if (!classeId) return;
    document.getElementById('listeAlertes').innerHTML = loadingHtml();
    document.getElementById('statsMatieres').innerHTML = loadingHtml();
    document.getElementById('listeElevesDash').innerHTML = loadingHtml();
    try {
        const data = await api('GET', `/api/dashboard/${classeId}`);
        currentDashboardClasseId = classeId;
        afficherAlertes(classeId);
        afficherStatsMatieres(data.stats);
        afficherElevesDash(data.eleves_list);
    } catch (e) {
        document.getElementById('listeAlertes').innerHTML =
            `<p class="msg-error" style="padding:8px">Erreur : ${escapeHtml(e.message)}</p>`;
        document.getElementById('statsMatieres').innerHTML = '';
        document.getElementById('listeElevesDash').innerHTML = '';
    }
}

async function afficherAlertes(classeId) {
    try {
        const data = await api('GET', '/api/alertes');
        const container = document.getElementById('listeAlertes');
        const alertes = classeId
            ? data.alertes.filter(a => a.classe_id == classeId)
            : data.alertes;
        if (!alertes.length) {
            container.innerHTML = '<p style="color:var(--gray-400)">Aucune alerte active</p>';
            return;
        }
        let html = alertes.map(a => {
            let cls = 'alerte-info';
            if (a.severite >= 4) cls = 'alerte-critique';
            else if (a.severite >= 2) cls = 'alerte-warning';
            return `<div class="alerte-item ${cls}">
                <div>
                    <strong>${escapeHtml(a.eleve_prenom)} ${escapeHtml(a.eleve_nom)}</strong>
                    ${a.matiere_nom ? `— ${escapeHtml(a.matiere_nom)}` : ''}
                    <br><span style="font-size:13px;color:var(--gray-600)">${escapeHtml(a.description)}</span>
                    <br><small>${escapeHtml(a.classe_nom)}</small>
                </div>
                <div style="display:flex;align-items:center;gap:6px">
                    <span class="badge-severite sev-${a.severite}">${a.severite}</span>
                    <button class="btn btn-sm btn-success" onclick="resoudreAlerte(${a.id})">Résolue</button>
                </div>
            </div>`;
        }).join('');
        if (alertes.length > 1) {
            html += `<div style="margin-top:10px;text-align:right">
                <button class="btn btn-sm btn-success" onclick="resoudreToutesAlertes(${classeId || 'null'})">
                    Résoudre toutes (${alertes.length})
                </button>
            </div>`;
        }
        container.innerHTML = html;
    } catch {}
}

async function resoudreToutesAlertes(classeId) {
    if (!confirm('Marquer toutes les alertes comme résolues ?')) return;
    try {
        await api('PUT', '/api/alertes/resolve-all', classeId ? { classe_id: parseInt(classeId) } : {});
        afficherAlertes(classeId);
        showToast('Toutes les alertes résolues', 'success');
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function resoudreAlerte(id) {
    await api('PUT', `/api/alertes/${id}/resolve`);
    afficherAlertes(currentDashboardClasseId);
}

// #18 — Résoudre depuis la fiche élève (modal)
async function resoudreAlerteDepuisFiche(alerteId, eleveId) {
    try {
        await api('PUT', `/api/alertes/${alerteId}/resolve`);
        showToast('Alerte résolue', 'success');
        ouvrirFicheEleve(eleveId);
    } catch (e) {
        showToast(e.message, 'error');
    }
}

function afficherStatsMatieres(stats) {
    const container = document.getElementById('statsMatieres');
    if (!stats.length) {
        container.innerHTML = '<p style="color:var(--gray-400)">Aucune note importée</p>';
        return;
    }
    container.innerHTML = `<table>
        <thead><tr><th>Matière</th><th>Coef</th><th>Moyenne</th><th>Min</th><th>Max</th><th>Notes</th></tr></thead>
        <tbody>
            ${stats.map(s => `
                <tr>
                    <td>${s.matiere}</td>
                    <td>${s.coefficient}</td>
                    <td class="${s.moyenne >= 14 ? 'perf-bon' : s.moyenne >= 10 ? 'perf-moyen' : 'perf-faible'}">${s.moyenne ? s.moyenne.toFixed(2) : '-'}</td>
                    <td>${s.min ?? '-'}</td>
                    <td>${s.max ?? '-'}</td>
                    <td>${s.nb_notes}</td>
                </tr>
            `).join('')}
        </tbody>
    </table>`;
}

function afficherElevesDash(eleves) {
    const container = document.getElementById('listeElevesDash');
    if (!eleves.length) {
        container.innerHTML = '<p style="color:var(--gray-400)">Aucun élève dans cette classe</p>';
        return;
    }
    container.innerHTML = `<table>
        <thead><tr><th>Matricule</th><th>Nom</th><th>Moyenne</th><th>Niveau</th><th>Alertes</th><th></th></tr></thead>
        <tbody>
            ${eleves.map(e => `
                <tr>
                    <td>${escapeHtml(e.matricule)}</td>
                    <td>${escapeHtml(e.nom)} ${escapeHtml(e.prenom)}</td>
                    <td class="perf-${e.niveau}">${e.moyenne !== null ? e.moyenne.toFixed(2) : '-'}</td>
                    <td><span class="badge badge-${e.niveau === 'bon' ? 'success' : e.niveau === 'moyen' ? 'warning' : e.niveau === 'faible' ? 'danger' : 'info'}">${e.niveau}</span></td>
                    <td>${e.alertes > 0 ? `<span class="badge badge-danger">${e.alertes}</span>` : '0'}</td>
                    <td><button class="btn btn-sm btn-primary" onclick="ouvrirFicheEleve(${e.id})">Fiche</button></td>
                </tr>
            `).join('')}
        </tbody>
    </table>`;
}

/* ════════════════════════════════════════════
   IMPORT DE NOTES
   ════════════════════════════════════════════ */
async function chargerMatieresImport() {
    const classeId = document.getElementById('inputImportClasse').value;
    const sel = document.getElementById('inputImportMatiere');
    if (!classeId) { sel.innerHTML = '<option value="">Matière...</option>'; return; }
    try {
        const data = await api('GET', `/api/classes/${classeId}`);
        sel.innerHTML = '<option value="">Matière...</option>' +
            (data.matieres || []).map(m => `<option value="${m.id}">${m.nom}</option>`).join('');
    } catch {}
}

async function previewImportNotes() {
    const classeId = document.getElementById('inputImportClasse').value;
    const matiereId = document.getElementById('inputImportMatiere').value;
    const fileInput = document.getElementById('inputFichierNotes');
    const container = document.getElementById('previewImport');
    const tableContainer = document.getElementById('previewTable');
    const confirmBtn = document.getElementById('btnConfirmerImport');
    const btn = document.getElementById('btnPreviewNotes');

    if (!classeId || !matiereId || !fileInput.files.length)
        return showToast('Sélectionnez classe, matière et fichier', 'warning');

    const form = new FormData();
    form.append('file', fileInput.files[0]);
    form.append('classe_id', classeId);
    form.append('matiere_id', matiereId);

    setLoading(btn, true);
    container.innerHTML = loadingHtml('Analyse en cours...');
    tableContainer.innerHTML = '';
    confirmBtn.style.display = 'none';

    try {
        const data = await api('POST', '/api/notes/import/preview', form);
        let html = `<strong>Matière : ${data.matiere}</strong><br>`;
        html += `<span class="msg-success">✅ ${data.preview.length} notes valides</span>`;

        if (data.warnings.length) {
            html += `<br><span class="msg-warning">⚠️ ${data.warnings.length} avertissement(s) :</span><ul>`;
            data.warnings.forEach(w => {
                html += `<li>Ligne ${w.ligne} : ${w.message} (${w.note}/20)</li>`;
            });
            html += '</ul>';
        }
        if (data.errors.length) {
            html += `<br><span class="msg-error">❌ ${data.errors.length} erreur(s) :</span><ul>`;
            data.errors.forEach(e => {
                html += `<li>Ligne ${e.ligne} : ${e.erreur}</li>`;
            });
            html += '</ul>';
        }

        container.innerHTML = html;

        if (data.preview.length) {
            tableContainer.innerHTML = `<table>
                <thead><tr><th>Matricule</th><th>Élève</th><th>Note</th><th>Date</th></tr></thead>
                <tbody>${data.preview.map(p => `<tr><td>${p.matricule}</td><td>${p.nom_eleve}</td><td>${p.note}/20</td><td>${p.date}</td></tr>`).join('')}</tbody>
            </table>`;
            confirmBtn.style.display = 'inline-block';
            confirmBtn.dataset.classeId = classeId;
            confirmBtn.dataset.matiereId = matiereId;
        } else {
            tableContainer.innerHTML = '';
            confirmBtn.style.display = 'none';
        }
    } catch (e) {
        msg(container, `Erreur: ${e.message}`, 'error');
        tableContainer.innerHTML = '';
        confirmBtn.style.display = 'none';
    } finally {
        setLoading(btn, false);
    }
}

async function confirmerImportNotes() {
    const btn = document.getElementById('btnConfirmerImport');
    const classeId = btn.dataset.classeId;
    const matiereId = btn.dataset.matiereId;
    const fileInput = document.getElementById('inputFichierNotes');

    const form = new FormData();
    form.append('file', fileInput.files[0]);
    form.append('classe_id', classeId);
    form.append('matiere_id', matiereId);

    setLoading(btn, true);
    try {
        const data = await api('POST', '/api/notes/import', form);
        const msgEl = document.getElementById('previewImport');
        if (!data.success) {
            let html = `<span class="msg-error">${data.errors.length} erreur(s) lors de l'import :</span><ul>`;
            data.errors.forEach(err => {
                html += `<li>Ligne ${err.ligne}${err.matricule ? ` (${err.matricule})` : ''} : ${err.erreur}</li>`;
            });
            html += '</ul>';
            msgEl.innerHTML = html;
            setLoading(btn, false);
        } else {
            const skippedMsg = data.skipped ? `, ${data.skipped} doublon(s) ignoré(s)` : '';
            const txt = `${data.count} notes importées${skippedMsg}, ${data.alertes} alerte(s) générée(s)`;
            msg(msgEl, txt, 'success');
            showToast(`${data.count} notes importées${skippedMsg}`, 'success');
            document.getElementById('previewTable').innerHTML = '';
            btn.style.display = 'none';
            fileInput.value = '';
        }
    } catch (e) {
        const msgEl = document.getElementById('previewImport');
        msg(msgEl, `Erreur: ${e.message}`, 'error');
        setLoading(btn, false);
    }
}

/* ════════════════════════════════════════════
   AJOUT MANUEL DE NOTE
   ════════════════════════════════════════════ */
async function chargerElevesManuel() {
    const classeId = document.getElementById('inputManuelClasse').value;
    const sel = document.getElementById('inputManuelEleve');
    const selMatiere = document.getElementById('inputManuelMatiere');
    if (!classeId) {
        sel.innerHTML = '<option value="">Élève...</option>';
        selMatiere.innerHTML = '<option value="">Matière...</option>';
        return;
    }
    try {
        const [classeData, elevesData] = await Promise.all([
            api('GET', `/api/classes/${classeId}`),
            api('GET', `/api/eleves/classe/${classeId}`)
        ]);
        sel.innerHTML = '<option value="">Élève...</option>' +
            elevesData.eleves.map(e => `<option value="${e.id}">${e.nom} ${e.prenom}</option>`).join('');
        selMatiere.innerHTML = '<option value="">Matière...</option>' +
            (classeData.matieres || []).map(m => `<option value="${m.id}">${m.nom}</option>`).join('');
    } catch (e) {
        sel.innerHTML = '<option value="">Erreur de chargement</option>';
    }
}

async function ajouterNoteManuelle() {
    const eleveId = document.getElementById('inputManuelEleve').value;
    const matiereId = document.getElementById('inputManuelMatiere').value;
    const note = parseFloat(document.getElementById('inputManuelNote').value);
    const date = document.getElementById('inputManuelDate').value;
    const btn = document.getElementById('btnAjouterNote');
    if (!eleveId || !matiereId || isNaN(note)) return showToast('Tous les champs sont requis', 'warning');
    setLoading(btn, true);
    try {
        const data = await api('POST', '/api/notes/manuel', {
            eleve_id: parseInt(eleveId),
            matiere_id: parseInt(matiereId),
            note, date
        });
        const txt = 'Note ajoutée !' + (data.alertes ? ` (${data.alertes} alerte(s))` : '');
        msg(document.getElementById('resultatManuel'), txt, 'success');
        showToast('Note ajoutée avec succès', 'success');
        document.getElementById('inputManuelNote').value = '';
    } catch (e) {
        msg(document.getElementById('resultatManuel'), `Erreur: ${e.message}`, 'error');
    } finally {
        setLoading(btn, false);
    }
}

/* ════════════════════════════════════════════
   GESTION ÉLÈVES
   ════════════════════════════════════════════ */

// #9 — Navigation par classe
async function parcourirClasse() {
    const classeId = document.getElementById('inputBrowseClasse').value;
    const container = document.getElementById('resultatsRecherche');
    document.getElementById('inputSearchEleve').value = '';
    if (!classeId) { container.innerHTML = ''; return; }
    container.innerHTML = loadingHtml();
    try {
        const data = await api('GET', `/api/eleves/classe/${classeId}`);
        if (!data.eleves.length) {
            container.innerHTML = '<p style="color:var(--gray-400);padding:12px">Aucun élève dans cette classe</p>';
            return;
        }
        container.innerHTML = data.eleves.map(e => `
            <div class="item-row" id="eleve-row-${e.id}">
                <span>
                    <strong>${escapeHtml(e.nom)} ${escapeHtml(e.prenom)}</strong>
                    <span style="color:var(--gray-400);margin-left:8px">${escapeHtml(e.matricule)}</span>
                </span>
                <div style="display:flex;gap:6px">
                    <button class="btn btn-sm btn-primary" onclick="ouvrirFicheEleve(${e.id})">Fiche</button>
                    <button class="btn btn-sm btn-danger" onclick="supprimerEleve(${e.id}, '${classeId}')">Suppr.</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<p class="msg-error" style="padding:8px">Erreur de chargement</p>';
    }
}

// #8 — Ajout individuel d'élève
async function ajouterEleve() {
    const classeId = parseInt(document.getElementById('inputAjoutClasse').value);
    const matricule = document.getElementById('inputAjoutMatricule').value.trim();
    const nom = document.getElementById('inputAjoutNom').value.trim();
    const prenom = document.getElementById('inputAjoutPrenom').value.trim();
    const date_naissance = document.getElementById('inputAjoutNaissance').value;
    const btn = document.getElementById('btnAjouterEleve');
    const res = document.getElementById('resultatAjoutEleve');
    if (!classeId || !matricule || !nom || !prenom) return showToast('Classe, matricule, nom et prénom requis', 'warning');
    setLoading(btn, true);
    try {
        await api('POST', '/api/eleves', { classe_id: classeId, matricule, nom, prenom, date_naissance });
        msg(res, `${nom} ${prenom} ajouté avec succès`, 'success');
        showToast(`${nom} ${prenom} ajouté`, 'success');
        document.getElementById('inputAjoutMatricule').value = '';
        document.getElementById('inputAjoutNom').value = '';
        document.getElementById('inputAjoutPrenom').value = '';
        document.getElementById('inputAjoutNaissance').value = '';
        chargerClassesDansSelects();
        if (document.getElementById('inputBrowseClasse').value == classeId) parcourirClasse();
    } catch (e) {
        msg(res, e.message, 'error');
    } finally {
        setLoading(btn, false);
    }
}

// #8 — Suppression d'élève
async function supprimerEleve(eleveId, classeId) {
    if (!confirm('Supprimer cet élève et toutes ses notes ?')) return;
    try {
        await api('DELETE', `/api/eleves/${eleveId}`);
        showToast('Élève supprimé', 'success');
        const row = document.getElementById(`eleve-row-${eleveId}`);
        if (row) row.remove();
        chargerClassesDansSelects();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

let searchTimeout = null;
function rechercherEleves() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
        const q = document.getElementById('inputSearchEleve').value.trim();
        document.getElementById('inputBrowseClasse').value = '';
        const container = document.getElementById('resultatsRecherche');
        if (q.length < 2) { container.innerHTML = ''; return; }
        try {
            const data = await api('GET', `/api/eleves/search?q=${encodeURIComponent(q)}`);
            if (!data.eleves.length) {
                container.innerHTML = '<p style="color:var(--gray-400)">Aucun résultat</p>';
                return;
            }
            container.innerHTML = data.eleves.map(e => `
                <div class="item-row">
                    <span><strong>${escapeHtml(e.nom)} ${escapeHtml(e.prenom)}</strong> — ${escapeHtml(e.matricule)} <span class="badge badge-info">${escapeHtml(e.classe_nom)}</span></span>
                    <button class="btn btn-sm btn-primary" onclick="ouvrirFicheEleve(${e.id})">Fiche</button>
                </div>
            `).join('');
        } catch (e) {
            container.innerHTML = '<p class="msg-error" style="padding:8px">Erreur de recherche</p>';
        }
    }, 300);
}

/* ════════════════════════════════════════════
   FICHE ÉLÈVE (MODAL)
   ════════════════════════════════════════════ */
async function ouvrirFicheEleve(eleveId) {
    const modal = document.getElementById('modalFicheEleve');
    modal.style.display = 'flex';
    modal.dataset.eleveId = eleveId;
    const body = document.getElementById('modalBody');
    body.innerHTML = '<p>Chargement...</p>';
    try {
        const data = await api('GET', `/api/dashboard/eleve/${eleveId}`);
        renderFicheEleve(data);
    } catch (e) {
        body.innerHTML = `<p class="msg-error">Erreur: ${e.message}</p>`;
    }
}

function fermerFiche() {
    document.getElementById('modalFicheEleve').style.display = 'none';
}

function renderFicheEleve(d) {
    const moyCls = d.moyenne_generale >= 14 ? 'perf-bon' : d.moyenne_generale >= 10 ? 'perf-moyen' : 'perf-faible';
    let html = `
        <div class="fiche-header">
            <div>
                <h2>${escapeHtml(d.prenom)} ${escapeHtml(d.nom)}</h2>
                <p>${escapeHtml(d.classe_nom)} — Matricule: ${escapeHtml(d.matricule)}</p>
            </div>
            <div class="fiche-moyenne ${moyCls}">${d.moyenne_generale ?? '-'}/20</div>
        </div>

        <div class="fiche-section">
            <h4>Tendances par matière</h4>
            <div class="tendance-grid">
                ${d.tendances.map(t => {
                    const trendIcon = t.trend === 'hausse' ? '&#8593;' : t.trend === 'baisse' ? '&#8595;' : '&#8594;';
                    return `<div class="tendance-card">
                        <div class="matiere-nom">${escapeHtml(t.matiere)} (coef: ${t.coefficient})</div>
                        <div class="matiere-moyenne ${'trend-' + t.trend}">${t.moyenne}/20</div>
                        <div style="font-size:24px" class="${'trend-' + t.trend}">${trendIcon}</div>
                        <small>${t.nb_notes} note(s)</small>
                    </div>`;
                }).join('')}
            </div>
        </div>

        <div class="fiche-section">
            <h4>Courbes de progression</h4>
            <div id="chartArea" style="height:300px"></div>
        </div>

        <div class="fiche-section">
            <h4>Historique des notes</h4>
            <div class="table-responsive">
                <table>
                    <thead><tr><th>Matière</th><th>Note</th><th>Date</th><th>Source</th><th>Actions</th></tr></thead>
                    <tbody>
                        ${d.notes.map(n => `
                            <tr id="note-row-${n.id}">
                                <td>${escapeHtml(n.matiere_nom)}</td>
                                <td id="note-val-${n.id}" class="${n.note >= 14 ? 'perf-bon' : n.note >= 10 ? 'perf-moyen' : 'perf-faible'}">${n.note}/20</td>
                                <td id="note-date-${n.id}">${n.date_note}</td>
                                <td>${n.source}</td>
                                <td id="note-actions-${n.id}" style="white-space:nowrap">
                                    <button class="btn btn-sm btn-primary" onclick="modifierNote(${n.id}, ${n.note}, '${n.date_note}')">Modifier</button>
                                    <button class="btn btn-sm btn-danger" onclick="supprimerNote(${n.id})">Suppr.</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="fiche-section">
            <h4>Alertes actives</h4>
            ${d.alertes.length ? d.alertes.map(a => {
                const cls = a.severite >= 4 ? 'alerte-critique' : a.severite >= 2 ? 'alerte-warning' : 'alerte-info';
                return `<div class="alerte-item ${cls}">
                    <div><strong>${escapeHtml(a.type_alerte)}</strong> — ${escapeHtml(a.description)}</div>
                    <div style="display:flex;align-items:center;gap:6px">
                        <span class="badge-severite sev-${a.severite}">${a.severite}</span>
                        <button class="btn btn-sm btn-success" onclick="resoudreAlerteDepuisFiche(${a.id}, ${d.id})">Résoudre</button>
                    </div>
                </div>`;
            }).join('') : '<p style="color:var(--gray-400)">Aucune alerte active</p>'}
        </div>
    `;
    document.getElementById('modalBody').innerHTML = html;

    // Graphique des courbes
    setTimeout(() => renderCourbes(d.courbes), 100);
}

function renderCourbes(courbes) {
    const container = document.getElementById('chartArea');
    if (!container) return;
    container.innerHTML = '<canvas id="chartCourbes"></canvas>';
    const ctx = document.getElementById('chartCourbes').getContext('2d');

    const datasets = [];
    const allLabels = [];
    const labelMap = {};
    const colors = ['#1e3a8a', '#16a34a', '#ea580c', '#dc2626', '#6b7280', '#8b5cf6', '#06b6d4', '#f59e0b'];

    // Collecter toutes les dates uniques et créer un index
    for (const [matiere, points] of Object.entries(courbes)) {
        if (!points.length) continue;
        points.forEach(p => {
            if (!labelMap[p.date]) {
                labelMap[p.date] = allLabels.length;
                allLabels.push(p.date);
            }
        });
    }

    // Trier les dates
    allLabels.sort((a, b) => a.localeCompare(b));
    allLabels.forEach((date, idx) => {
        labelMap[date] = idx;
    });

    let i = 0;
    for (const [matiere, points] of Object.entries(courbes)) {
        if (!points.length) continue;
        const sorted = points.sort((a, b) => a.date.localeCompare(b.date));
        
        // Créer un tableau avec tous les points mais null pour les dates manquantes
        const dataArray = new Array(allLabels.length).fill(null);
        sorted.forEach(p => {
            dataArray[labelMap[p.date]] = p.note;
        });

        datasets.push({
            label: matiere,
            data: dataArray,
            borderColor: colors[i % colors.length],
            backgroundColor: colors[i % colors.length] + '33',
            fill: false,
            tension: 0.4,
            spanGaps: true,
            pointRadius: 5,
            pointHoverRadius: 7,
            pointBackgroundColor: colors[i % colors.length],
            pointBorderColor: '#fff',
            pointBorderWidth: 2
        });
        i++;
    }

    if (!datasets.length) {
        container.innerHTML = '<p style="color:var(--gray-400);padding:20px;text-align:center">Aucune donnée de notes</p>';
        return;
    }

    new Chart(ctx, {
        type: 'line',
        data: { 
            labels: allLabels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'Date', font: { weight: 'bold' } },
                    ticks: { maxTicksLimit: 10 }
                },
                y: {
                    min: 0,
                    max: 20,
                    title: { display: true, text: 'Note /20', font: { weight: 'bold' } },
                    ticks: { stepSize: 2 }
                }
            },
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { weight: 'bold' },
                    callbacks: {
                        afterLabel: function(context) {
                            return 'Date: ' + allLabels[context.dataIndex];
                        }
                    }
                }
            }
        }
    });
}

/* ════════════════════════════════════════════
   RAPPORTS
   ════════════════════════════════════════════ */
async function chargerRapports() {
    const classeId = document.getElementById('inputRapportClasse').value;
    if (!classeId) return;
    document.getElementById('syntheseClasse').innerHTML = loadingHtml();
    document.getElementById('rapportDetails').innerHTML = '';
    document.getElementById('btnExportCSV').style.display = 'none';
    try {
        const data = await api('GET', `/api/dashboard/${classeId}`);
        rapportData = data;
        document.getElementById('btnExportCSV').style.display = 'inline-block';
        const synthese = document.getElementById('syntheseClasse');
        const nbEleves = data.eleves_list.length;
        const nbAlertes = data.alertes_count;

        // Statistiques
        const moyennes = data.eleves_list.filter(e => e.moyenne !== null).map(e => e.moyenne);
        const moyenneClasse = moyennes.length ? (moyennes.reduce((a, b) => a + b, 0) / moyennes.length) : 0;
        const nbBon = data.eleves_list.filter(e => e.niveau === 'bon').length;
        const nbMoyen = data.eleves_list.filter(e => e.niveau === 'moyen').length;
        const nbFaible = data.eleves_list.filter(e => e.niveau === 'faible').length;

        synthese.innerHTML = `
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px">
                <div class="tendance-card"><div class="matiere-nom">Élèves</div><div class="matiere-moyenne">${nbEleves}</div></div>
                <div class="tendance-card"><div class="matiere-nom">Moyenne classe</div><div class="matiere-moyenne">${moyenneClasse.toFixed(2)}</div></div>
                <div class="tendance-card"><div class="matiere-nom" style="color:var(--success)">Bon niveau</div><div class="matiere-moyenne">${nbBon}</div></div>
                <div class="tendance-card"><div class="matiere-nom" style="color:var(--warning)">Moyen</div><div class="matiere-moyenne">${nbMoyen}</div></div>
                <div class="tendance-card"><div class="matiere-nom" style="color:var(--danger)">Faible</div><div class="matiere-moyenne">${nbFaible}</div></div>
                <div class="tendance-card"><div class="matiere-nom">Alertes</div><div class="matiere-moyenne" style="color:${nbAlertes > 0 ? 'var(--danger)' : 'var(--success)'}">${nbAlertes}</div></div>
            </div>
        `;

        // Graphique distribution
        if (distributionChart) distributionChart.destroy();
        const ctx = document.getElementById('chartDistribution').getContext('2d');
        distributionChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Bon (≥14)', 'Moyen (10-14)', 'Faible (<10)', 'Aucune note'],
                datasets: [{
                    label: 'Élèves',
                    data: [nbBon, nbMoyen, nbFaible, nbEleves - nbBon - nbMoyen - nbFaible],
                    backgroundColor: ['#16a34a', '#ea580c', '#dc2626', '#9ca3af']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: { display: true, text: 'Distribution des niveaux' }
                },
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: 'Nombre d\'élèves' } }
                }
            }
        });

        // Détails des stats par matière
        if (data.stats.length) {
            document.getElementById('rapportDetails').innerHTML = `<table>
                <thead><tr><th>Matière</th><th>Coef</th><th>Moyenne</th><th>Écart-type</th><th>Min</th><th>Max</th><th>Notes</th></tr></thead>
                <tbody>${data.stats.map(s => `
                    <tr>
                        <td>${s.matiere}</td>
                        <td>${s.coefficient}</td>
                        <td class="${s.moyenne >= 14 ? 'perf-bon' : s.moyenne >= 10 ? 'perf-moyen' : 'perf-faible'}">${s.moyenne != null ? s.moyenne.toFixed(2) : '-'}</td>
                        <td style="color:var(--gray-600)">${s.ecart_type != null ? s.ecart_type.toFixed(2) : '-'}</td>
                        <td>${s.min ?? '-'}</td>
                        <td>${s.max ?? '-'}</td>
                        <td>${s.nb_notes}</td>
                    </tr>
                `).join('')}</tbody>
            </table>`;
        } else {
            document.getElementById('rapportDetails').innerHTML = '<p style="color:var(--gray-400)">Aucune note importée</p>';
        }
    } catch (e) {
        document.getElementById('syntheseClasse').innerHTML =
            `<p class="msg-error" style="padding:8px">Erreur de chargement : ${escapeHtml(e.message)}</p>`;
    }
}

/* ════════════════════════════════════════════
   MODIFICATION / SUPPRESSION DE NOTE
   ════════════════════════════════════════════ */
function modifierNote(noteId, noteVal, dateNote) {
    const inputStyle = 'padding:4px;border:1px solid var(--gray-300);border-radius:4px';
    document.getElementById(`note-val-${noteId}`).innerHTML =
        `<input type="number" id="edit-note-${noteId}" value="${noteVal}" min="0" max="20" step="0.5" style="width:65px;${inputStyle}">`;
    document.getElementById(`note-date-${noteId}`).innerHTML =
        `<input type="date" id="edit-date-${noteId}" value="${dateNote}" style="${inputStyle}">`;
    document.getElementById(`note-actions-${noteId}`).innerHTML = `
        <button class="btn btn-sm btn-success" onclick="sauverNote(${noteId})">Sauver</button>
        <button class="btn btn-sm" style="background:var(--gray-200);color:var(--gray-700)" onclick="annulerModifNote()">×</button>
    `;
}

async function sauverNote(noteId) {
    const noteVal = parseFloat(document.getElementById(`edit-note-${noteId}`).value);
    const dateNote = document.getElementById(`edit-date-${noteId}`).value;
    if (isNaN(noteVal) || noteVal < 0 || noteVal > 20) return showToast('Note invalide (0-20)', 'warning');
    try {
        await api('PUT', `/api/notes/${noteId}`, { note: noteVal, date: dateNote });
        showToast('Note modifiée', 'success');
        const eleveId = document.getElementById('modalFicheEleve').dataset.eleveId;
        ouvrirFicheEleve(parseInt(eleveId));
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function supprimerNote(noteId) {
    if (!confirm('Supprimer cette note ?')) return;
    try {
        await api('DELETE', `/api/notes/${noteId}`);
        showToast('Note supprimée', 'success');
        const eleveId = document.getElementById('modalFicheEleve').dataset.eleveId;
        ouvrirFicheEleve(parseInt(eleveId));
    } catch (e) {
        showToast(e.message, 'error');
    }
}

function annulerModifNote() {
    const eleveId = document.getElementById('modalFicheEleve').dataset.eleveId;
    ouvrirFicheEleve(parseInt(eleveId));
}

/* ════════════════════════════════════════════
   EXPORT CSV RAPPORTS
   ════════════════════════════════════════════ */
function exporterRapportCSV() {
    if (!rapportData) return showToast('Chargez d\'abord un rapport', 'warning');
    const classeNom = document.getElementById('inputRapportClasse').selectedOptions[0]?.text || 'classe';
    const date = new Date().toLocaleDateString('fr-FR');

    const lignes = [
        [`GestNote — Rapport`, classeNom, date],
        [],
        ['=== STATISTIQUES PAR MATIÈRE ==='],
        ['Matière', 'Coefficient', 'Moyenne', 'Écart-type', 'Min', 'Max', 'Nb notes'],
        ...rapportData.stats.map(s => [
            s.matiere, s.coefficient,
            s.moyenne != null ? s.moyenne.toFixed(2) : '-',
            s.ecart_type != null ? s.ecart_type.toFixed(2) : '-',
            s.min ?? '-', s.max ?? '-', s.nb_notes
        ]),
        [],
        ['=== ÉLÈVES ==='],
        ['Matricule', 'Nom', 'Prénom', 'Moyenne générale', 'Niveau', 'Alertes actives'],
        ...rapportData.eleves_list.map(e => [
            e.matricule, e.nom, e.prenom,
            e.moyenne != null ? e.moyenne.toFixed(2) : '-',
            e.niveau, e.alertes
        ])
    ];

    const csv = '﻿' + lignes
        .map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(','))
        .join('\r\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rapport_${classeNom.replace(/\s+/g, '_')}_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Fermer la modale en cliquant dehors
document.addEventListener('click', (e) => {
    const modal = document.getElementById('modalFicheEleve');
    if (e.target === modal) fermerFiche();
});

// Touche Escape pour fermer la modale
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') fermerFiche();
});