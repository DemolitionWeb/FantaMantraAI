"""Mercato dal vivo: regole della lega, aggiudicazioni, svincoli, annulla.

Crediti residui di una squadra:
    budget iniziale + bonus riparazione
    - costo dei giocatori in rosa
    - crediti persi con gli svincoli (costo pagato - rimborso)

Rimborso di uno svincolo:
    - giocatore ancora in Serie A: una quota del costo (di default la metà,
      arrotondata per difetto: pagato 2 -> rimborso 1, pagato 5 -> 2);
    - giocatore che ha lasciato il campionato: costo pieno.
"""

import math
from datetime import datetime, timezone

from db.database import get_connection


REGOLE_PREDEFINITE = {
    "budget_iniziale": 500,
    "bonus_riparazione": 0,
    "max_giocatori": 30,
    "quota_rimborso": 0.5,
    "arrotondamento": "difetto",   # "difetto" oppure "eccesso"
}


class ErroreMercato(ValueError):
    """Operazione non consentita dalle regole (messaggio per l'utente)."""


def _adesso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------
# Regole
# ---------------------------------------------------------------------

def leggi_regole():
    conn = get_connection()
    try:
        salvate = dict(conn.execute("SELECT chiave, valore FROM impostazioni_lega"))
    finally:
        conn.close()

    regole = {}
    for chiave, predefinito in REGOLE_PREDEFINITE.items():
        valore = salvate.get(chiave)
        if valore is None:
            regole[chiave] = predefinito
        elif isinstance(predefinito, int):
            regole[chiave] = int(float(valore))
        elif isinstance(predefinito, float):
            regole[chiave] = float(valore)
        else:
            regole[chiave] = valore
    return regole


def salva_regole(**nuove):
    sconosciute = set(nuove) - set(REGOLE_PREDEFINITE)
    if sconosciute:
        raise ValueError(f"Regole sconosciute: {', '.join(sorted(sconosciute))}")

    conn = get_connection()
    try:
        conn.executemany(
            "INSERT OR REPLACE INTO impostazioni_lega (chiave, valore) VALUES (?, ?)",
            [(chiave, str(valore)) for chiave, valore in nuove.items()],
        )
        conn.commit()
    finally:
        conn.close()


def calcola_rimborso(costo, ha_lasciato_serie_a, regole=None):
    regole = regole or leggi_regole()
    if ha_lasciato_serie_a:
        return int(costo)
    quota = costo * regole["quota_rimborso"]
    arrotonda = math.ceil if regole["arrotondamento"] == "eccesso" else math.floor
    return int(arrotonda(quota))


# ---------------------------------------------------------------------
# Situazione delle squadre
# ---------------------------------------------------------------------

def situazione_squadre(regole=None):
    """Per ogni squadra: giocatori, spesi, persi con svincoli, residui,
    posti liberi e offerta massima, secondo le regole della lega."""
    regole = regole or leggi_regole()
    disponibili = regole["budget_iniziale"] + regole["bonus_riparazione"]

    conn = get_connection()
    try:
        righe = conn.execute(
            """
            SELECT f.id, f.nome, f.mia,
                   (SELECT COUNT(*) FROM rose_lega r WHERE r.fantasquadra_id = f.id),
                   (SELECT COALESCE(SUM(costo), 0) FROM rose_lega r
                     WHERE r.fantasquadra_id = f.id),
                   (SELECT COALESCE(SUM(costo - rimborso), 0) FROM movimenti_lega m
                     WHERE m.fantasquadra_id = f.id AND m.tipo = 'svincolo'
                       AND m.annullato = 0)
            FROM fantasquadre f
            ORDER BY f.nome COLLATE NOCASE
            """
        ).fetchall()
    finally:
        conn.close()

    situazione = []
    for squadra_id, nome, mia, giocatori, spesi, persi in righe:
        residui = disponibili - spesi - persi
        posti = max(regole["max_giocatori"] - giocatori, 0)
        # Va conservato 1 credito per ogni altro posto ancora libero.
        massima = max(0, residui - (posti - 1)) if posti else 0
        situazione.append({
            "id": squadra_id, "squadra": nome, "mia": bool(mia),
            "giocatori": giocatori, "spesi": spesi, "persi_svincoli": persi,
            "residui": residui, "posti_liberi": posti, "offerta_massima": massima,
        })
    return situazione


def _squadra(conn, nome):
    riga = conn.execute(
        "SELECT id FROM fantasquadre WHERE nome = ?", (nome,)
    ).fetchone()
    if not riga:
        raise ErroreMercato(f"La squadra '{nome}' non esiste nella lega.")
    return riga[0]


def _nome_giocatore(conn, giocatore_id):
    riga = conn.execute(
        "SELECT nome FROM giocatori WHERE id = ?", (giocatore_id,)
    ).fetchone()
    if not riga:
        raise ErroreMercato("Giocatore non trovato.")
    return riga[0]


# ---------------------------------------------------------------------
# Operazioni
# ---------------------------------------------------------------------

def aggiudica(giocatore_id, squadra, prezzo):
    """Assegna un giocatore svincolato a una squadra per `prezzo` crediti."""
    prezzo = int(prezzo)
    if prezzo < 1:
        raise ErroreMercato("Il prezzo deve essere almeno 1 credito.")

    situazione = {s["squadra"]: s for s in situazione_squadre()}
    if squadra not in situazione:
        raise ErroreMercato(f"La squadra '{squadra}' non esiste nella lega.")
    dati = situazione[squadra]

    conn = get_connection()
    try:
        nome = _nome_giocatore(conn, giocatore_id)
        possessore = conn.execute(
            """
            SELECT f.nome FROM rose_lega r
            JOIN fantasquadre f ON f.id = r.fantasquadra_id
            WHERE r.giocatore_id = ?
            """,
            (giocatore_id,),
        ).fetchone()
        if possessore:
            raise ErroreMercato(f"{nome} appartiene già a {possessore[0]}.")
        if dati["posti_liberi"] == 0:
            raise ErroreMercato(f"{squadra} ha già la rosa completa.")
        if prezzo > dati["offerta_massima"]:
            raise ErroreMercato(
                f"{squadra} può offrire al massimo {dati['offerta_massima']} crediti."
            )

        adesso = _adesso()
        conn.execute(
            "INSERT INTO rose_lega (giocatore_id, fantasquadra_id, costo,"
            " ultimo_aggiornamento) VALUES (?, ?, ?, ?)",
            (giocatore_id, dati["id"], prezzo, adesso),
        )
        conn.execute(
            "INSERT INTO movimenti_lega (momento, tipo, giocatore_id,"
            " fantasquadra_id, costo) VALUES (?, 'acquisto', ?, ?, ?)",
            (adesso, giocatore_id, dati["id"], prezzo),
        )
        conn.commit()
    finally:
        conn.close()

    return f"{nome} a {squadra} per {prezzo} crediti."


def svincola(giocatore_id, ha_lasciato_serie_a=None):
    """Svincola un giocatore e restituisce i crediti secondo le regole.

    Se `ha_lasciato_serie_a` è None si deduce dal listone: chi non c'è più
    ha lasciato il campionato e riceve il rimborso pieno.
    """
    conn = get_connection()
    try:
        nome = _nome_giocatore(conn, giocatore_id)
        riga = conn.execute(
            """
            SELECT r.fantasquadra_id, f.nome, r.costo
            FROM rose_lega r JOIN fantasquadre f ON f.id = r.fantasquadra_id
            WHERE r.giocatore_id = ?
            """,
            (giocatore_id,),
        ).fetchone()
        if not riga:
            raise ErroreMercato(f"{nome} non è in nessuna rosa.")
        squadra_id, squadra, costo = riga

        if ha_lasciato_serie_a is None:
            ha_lasciato_serie_a = not conn.execute(
                "SELECT 1 FROM listone WHERE giocatore_id = ?", (giocatore_id,)
            ).fetchone()

        rimborso = calcola_rimborso(costo or 0, ha_lasciato_serie_a)
        conn.execute("DELETE FROM rose_lega WHERE giocatore_id = ?", (giocatore_id,))
        conn.execute(
            "INSERT INTO movimenti_lega (momento, tipo, giocatore_id,"
            " fantasquadra_id, costo, rimborso) VALUES (?, 'svincolo', ?, ?, ?, ?)",
            (_adesso(), giocatore_id, squadra_id, costo or 0, rimborso),
        )
        conn.commit()
    finally:
        conn.close()

    motivo = "ha lasciato la Serie A, rimborso pieno" if ha_lasciato_serie_a else "rimborso parziale"
    return f"{nome} svincolato da {squadra}: {rimborso} crediti restituiti ({motivo})."


def annulla_ultimo():
    """Annulla l'ultimo acquisto o svincolo non ancora annullato."""
    conn = get_connection()
    try:
        movimento = conn.execute(
            """
            SELECT id, tipo, giocatore_id, fantasquadra_id, costo
            FROM movimenti_lega WHERE annullato = 0
            ORDER BY id DESC LIMIT 1
            """
        ).fetchone()
        if not movimento:
            raise ErroreMercato("Non ci sono operazioni da annullare.")

        movimento_id, tipo, giocatore_id, squadra_id, costo = movimento
        nome = _nome_giocatore(conn, giocatore_id)

        if tipo == "acquisto":
            conn.execute(
                "DELETE FROM rose_lega WHERE giocatore_id = ? AND fantasquadra_id = ?",
                (giocatore_id, squadra_id),
            )
        else:
            if conn.execute(
                "SELECT 1 FROM rose_lega WHERE giocatore_id = ?", (giocatore_id,)
            ).fetchone():
                raise ErroreMercato(
                    f"{nome} è stato poi acquistato da un'altra squadra: "
                    "annulla prima quell'acquisto."
                )
            conn.execute(
                "INSERT INTO rose_lega (giocatore_id, fantasquadra_id, costo,"
                " ultimo_aggiornamento) VALUES (?, ?, ?, ?)",
                (giocatore_id, squadra_id, costo, _adesso()),
            )

        conn.execute(
            "UPDATE movimenti_lega SET annullato = 1 WHERE id = ?", (movimento_id,)
        )
        conn.commit()
    finally:
        conn.close()

    return f"Annullato: {'acquisto' if tipo == 'acquisto' else 'svincolo'} di {nome}."


def rosa_squadra(squadra):
    """Giocatori di una squadra della lega, anche quelli non più nel
    listone (`in_serie_a` falso: rimborso pieno se svincolati)."""
    conn = get_connection()
    try:
        righe = conn.execute(
            """
            SELECT g.id, g.nome, g.squadra, r.costo, l.giocatore_id IS NOT NULL
            FROM rose_lega r
            JOIN fantasquadre f ON f.id = r.fantasquadra_id
            JOIN giocatori g ON g.id = r.giocatore_id
            LEFT JOIN listone l ON l.giocatore_id = r.giocatore_id
            WHERE f.nome = ?
            ORDER BY g.nome COLLATE NOCASE
            """,
            (squadra,),
        ).fetchall()
    finally:
        conn.close()

    return [
        {"giocatore_id": gid, "nome": nome, "squadra": club, "costo": costo,
         "in_serie_a": bool(in_serie_a)}
        for gid, nome, club, costo, in_serie_a in righe
    ]


def elenco_listone():
    """Tutti i giocatori del listone, per la ricerca durante l'asta."""
    conn = get_connection()
    try:
        righe = conn.execute(
            """
            SELECT giocatore_id, nome, squadra, ruoli_mantra
            FROM listone ORDER BY nome COLLATE NOCASE
            """
        ).fetchall()
    finally:
        conn.close()

    return [
        {"giocatore_id": gid, "nome": nome, "squadra": squadra, "ruoli_mantra": ruoli}
        for gid, nome, squadra, ruoli in righe
    ]


def storico_movimenti(limite=20):
    conn = get_connection()
    try:
        righe = conn.execute(
            """
            SELECT m.momento, m.tipo, g.nome, f.nome, m.costo, m.rimborso, m.annullato
            FROM movimenti_lega m
            JOIN giocatori g ON g.id = m.giocatore_id
            JOIN fantasquadre f ON f.id = m.fantasquadra_id
            ORDER BY m.id DESC LIMIT ?
            """,
            (limite,),
        ).fetchall()
    finally:
        conn.close()

    return [
        {"momento": momento, "tipo": tipo, "giocatore": giocatore,
         "squadra": squadra, "costo": costo, "rimborso": rimborso,
         "annullato": bool(annullato)}
        for momento, tipo, giocatore, squadra, costo, rimborso, annullato in righe
    ]
