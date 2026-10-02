import pandas as pd
import sqlite3 
from pathlib import Path


def get_connection():
    return sqlite3.connect(Path("database.db"))


def inizializza_rosa():
    """Crea la tabella locale usata per salvare la rosa d'asta."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS rosa_asta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            giocatore TEXT NOT NULL,
            squadra TEXT NOT NULL,
            ruoli TEXT NOT NULL,
            costo REAL NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def carica_rosa():
    """Carica la rosa salvata oppure restituisce una rosa vuota."""
    inizializza_rosa()
    conn = get_connection()

    rosa = pd.read_sql_query(
        """
        SELECT giocatore, squadra, ruoli, costo
        FROM rosa_asta
        ORDER BY id
        """,
        conn,
    )
    conn.close()

    if rosa.empty:
        return crea_rosa_vuota()

    return rosa


def salva_rosa(rosa):
    """Sostituisce il contenuto persistito con la rosa corrente."""
    inizializza_rosa()
    conn = get_connection()

    conn.execute("DELETE FROM rosa_asta")
    conn.executemany(
        """
        INSERT INTO rosa_asta (giocatore, squadra, ruoli, costo)
        VALUES (?, ?, ?, ?)
        """,
        rosa[["giocatore", "squadra", "ruoli", "costo"]].itertuples(
            index=False,
            name=None,
        ),
    )
    conn.commit()
    conn.close()


def crea_rosa_vuota():
    return pd.DataFrame(
        columns=[
            "giocatore",
            "squadra",
            "ruoli",
            "costo",
        ]
    )


def crea_storico_asta():
    return pd.DataFrame(
        columns=[
            "giocatore",
            "squadra",
            "ruoli",
            "prezzo",
            "acquirente",
        ]
    )


def aggiungi_giocatore(rosa, giocatore, squadra, ruoli, costo):
    nuovo_giocatore = pd.DataFrame(
        [
            {
                "giocatore": giocatore,
                "squadra": squadra,
                "ruoli": ruoli,
                "costo": costo,
            }
        ]
    )

    return pd.concat(
        [rosa, nuovo_giocatore],
        ignore_index=True,
    )


def conta_ruoli(rosa):
    conteggio = {
        "POR": 0,
        "DC": 0,
        "DD": 0,
        "DS": 0,
        "B": 0,
        "E": 0,
        "M": 0,
        "C": 0,
        "W": 0,
        "T": 0,
        "A": 0,
        "PC": 0,
    }

    for _, giocatore in rosa.iterrows():
        ruoli = giocatore["ruoli"]

        if not isinstance(ruoli, str):
            continue

        ruoli = ruoli.upper().replace(" ", "").split(",")

        for ruolo in ruoli:
            if ruolo in conteggio:
                conteggio[ruolo] += 1

    return conteggio

def salva_presenze(presenze):
    conn = get_connection()
    cursor = conn.cursor()

    for presenza in presenze:
        cursor.execute(
            """
            DELETE FROM presenze
            WHERE giocatore_id = ?
            AND partita_id = ?
            """,
            (
                presenza["giocatore_id"],
                presenza["partita_id"],
            ),
        )

        cursor.execute(
            """
            INSERT INTO presenze (
                giocatore_id,
                partita_id,
                titolare,
                minuti,
                posizione,
                numero_maglia,
                voto,
                gol,
                assist,
                ammonizioni,
                espulsioni
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                presenza["giocatore_id"],
                presenza["partita_id"],
                presenza["titolare"],
                presenza["minuti"],
                presenza["posizione"],
                presenza["numero_maglia"],
                presenza["voto"],
                presenza["gol"],
                presenza["assist"],
                presenza["ammonizioni"],
                presenza["espulsioni"],
            ),
        )

    conn.commit()
    conn.close()
