"""Rose di tutte le squadre della lega e giocatori svincolati.

Le rose arrivano dall'esportazione Excel di Leghe Fantacalcio: un foglio
con, per ogni squadra, una colonna "nome squadra" e una "costo", separate
da una colonna vuota, e una riga "totale" in fondo. I giocatori vengono
collegati al listone (va importato prima) tramite il nome.
"""

import unicodedata
from datetime import datetime, timezone

from openpyxl import load_workbook

from db.database import get_connection


def _chiave(nome):
    testo = unicodedata.normalize("NFKD", str(nome or "")).casefold()
    testo = "".join(c for c in testo if not unicodedata.combining(c))
    return " ".join(testo.split())


def leggi_rose_xlsx(percorso):
    """Restituisce {squadra: {"giocatori": [(nome, costo)], "totale": n}}."""
    foglio = load_workbook(percorso, read_only=True, data_only=True).worksheets[0]
    righe = [list(r) for r in foglio.iter_rows(values_only=True)]
    if not righe:
        return {}

    intestazione = righe[0]
    colonne = [
        (indice, str(valore).strip())
        for indice, valore in enumerate(intestazione)
        if valore not in (None, "") and str(valore).strip().casefold() != "costo"
    ]

    rose = {}
    for indice, squadra in colonne:
        giocatori, totale = [], None
        for riga in righe[1:]:
            nome = riga[indice] if indice < len(riga) else None
            costo = riga[indice + 1] if indice + 1 < len(riga) else None
            if nome in (None, ""):
                continue
            nome = str(nome).strip()
            costo = int(float(costo)) if costo not in (None, "") else 0
            if nome.casefold() == "totale":
                totale = costo
            else:
                giocatori.append((nome, costo))
        rose[squadra] = {"giocatori": giocatori, "totale": totale}

    return rose


def importa_rose(percorso, mia_squadra=None):
    """Sostituisce le rose della lega con quelle del file.

    `mia_squadra`: nome della propria squadra. Se manca, viene scelta la
    squadra con più giocatori in comune con la tabella `rosa`.
    """
    rose = leggi_rose_xlsx(percorso)
    if not rose:
        raise ValueError(f"Nessuna rosa letta da {percorso}.")

    adesso = datetime.now(timezone.utc).isoformat()
    riepilogo = {"squadre": len(rose), "giocatori": 0, "non_trovati": [],
                 "ambigui": [], "totali_diversi": [], "mia": None}

    conn = get_connection()
    try:
        indice = {}
        for gid, nome in conn.execute("SELECT giocatore_id, nome FROM listone"):
            indice.setdefault(_chiave(nome), []).append(gid)
        if not indice:
            raise ValueError("Listone vuoto: importa prima il listone.")

        in_rosa = {r[0] for r in conn.execute("SELECT giocatore_id FROM rosa")}

        conn.execute("DELETE FROM rose_lega")
        conn.execute("UPDATE fantasquadre SET mia = 0")

        sovrapposizione = {}
        for squadra, dati in rose.items():
            conn.execute(
                "INSERT OR IGNORE INTO fantasquadre (nome) VALUES (?)", (squadra,)
            )
            squadra_id = conn.execute(
                "SELECT id FROM fantasquadre WHERE nome = ?", (squadra,)
            ).fetchone()[0]

            speso = 0
            for nome, costo in dati["giocatori"]:
                speso += costo
                trovati = indice.get(_chiave(nome), [])
                if not trovati:
                    riepilogo["non_trovati"].append((squadra, nome))
                    continue
                if len(trovati) > 1:
                    riepilogo["ambigui"].append((squadra, nome))
                    continue
                conn.execute(
                    "INSERT OR REPLACE INTO rose_lega (giocatore_id,"
                    " fantasquadra_id, costo, ultimo_aggiornamento)"
                    " VALUES (?, ?, ?, ?)",
                    (trovati[0], squadra_id, costo, adesso),
                )
                riepilogo["giocatori"] += 1
                if trovati[0] in in_rosa:
                    sovrapposizione[squadra] = sovrapposizione.get(squadra, 0) + 1

            if dati["totale"] is not None and dati["totale"] != speso:
                riepilogo["totali_diversi"].append((squadra, speso, dati["totale"]))

        mia = mia_squadra or (
            max(sovrapposizione, key=sovrapposizione.get) if sovrapposizione else None
        )
        if mia:
            if mia not in rose:
                raise ValueError(f"La squadra '{mia}' non è nel file delle rose.")
            conn.execute("UPDATE fantasquadre SET mia = 1 WHERE nome = ?", (mia,))
            riepilogo["mia"] = mia

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return riepilogo


def riepilogo_squadre(budget=500):
    """Giocatori, crediti spesi e residui di ogni squadra della lega."""
    conn = get_connection()
    try:
        righe = conn.execute(
            """
            SELECT f.nome, f.mia, COUNT(r.giocatore_id), COALESCE(SUM(r.costo), 0)
            FROM fantasquadre f
            LEFT JOIN rose_lega r ON r.fantasquadra_id = f.id
            GROUP BY f.id
            ORDER BY f.nome COLLATE NOCASE
            """
        ).fetchall()
    finally:
        conn.close()

    return [
        {"squadra": nome, "mia": bool(mia), "giocatori": numero,
         "spesi": spesi, "residui": budget - spesi}
        for nome, mia, numero, spesi in righe
    ]


def svincolati(ruolo_mantra=None):
    """Giocatori del listone non presenti in nessuna rosa della lega,
    ordinati per FVM Mantra decrescente."""
    conn = get_connection()
    try:
        righe = conn.execute(
            """
            SELECT l.giocatore_id, l.nome, l.squadra, l.ruoli_mantra,
                   l.qa_mantra, l.fvm_mantra, l.fanta_media, l.presenze
            FROM listone l
            LEFT JOIN rose_lega r ON r.giocatore_id = l.giocatore_id
            WHERE r.giocatore_id IS NULL
            ORDER BY l.fvm_mantra DESC, l.nome
            """
        ).fetchall()
    finally:
        conn.close()

    risultato = []
    for gid, nome, squadra, ruoli, qa, fvm, fanta_media, presenze in righe:
        if ruolo_mantra and ruolo_mantra.upper() not in (ruoli or "").split(", "):
            continue
        risultato.append({
            "giocatore_id": gid, "nome": nome, "squadra": squadra,
            "ruoli_mantra": ruoli, "quotazione": qa, "fvm": fvm,
            "fanta_media": fanta_media, "presenze": presenze,
        })
    return risultato
