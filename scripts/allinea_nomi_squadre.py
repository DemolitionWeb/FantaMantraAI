"""Riporta ai nomi canonici le squadre già salvate nel database.

Aggiorna partite (casa e trasferta), giocatori e classifica. Gli ID dei
giocatori non vengono modificati, per non rompere i collegamenti con
rosa, presenze e infortuni. Si può rilanciare senza effetti collaterali.

Uso (dalla cartella del progetto):
    python -m scripts.allinea_nomi_squadre
"""

import sqlite3

from db.database import crea_database, get_connection
from squadre import nome_canonico


def _allinea_colonna(conn, tabella, colonna, chiave):
    modifiche = []
    righe = conn.execute(
        f"SELECT {chiave}, {colonna} FROM {tabella} WHERE {colonna} IS NOT NULL"
    ).fetchall()

    for identificativo, nome in righe:
        canonico = nome_canonico(nome)
        if canonico != nome:
            conn.execute(
                f"UPDATE {tabella} SET {colonna} = ? WHERE {chiave} = ?",
                (canonico, identificativo),
            )
            modifiche.append((nome, canonico))

    return modifiche


def allinea():
    """Allinea i nomi e restituisce {tabella.colonna: [(prima, dopo), ...]}."""
    crea_database()
    conn = get_connection()
    risultato = {}

    try:
        for tabella, colonna, chiave in (
            ("partite", "squadra_casa", "id"),
            ("partite", "squadra_trasferta", "id"),
            ("giocatori", "squadra", "id"),
            ("classifica", "squadra", "rowid"),
        ):
            risultato[f"{tabella}.{colonna}"] = _allinea_colonna(
                conn, tabella, colonna, chiave
            )
        conn.commit()
    except sqlite3.IntegrityError:
        # Es. due partite identiche salvate con nomi diversi: nessuna
        # modifica parziale, il database resta com'era.
        conn.rollback()
        raise
    finally:
        conn.close()

    return risultato


def main():
    risultato = allinea()
    totale = sum(len(modifiche) for modifiche in risultato.values())

    for campo, modifiche in risultato.items():
        if not modifiche:
            continue
        conteggio = {}
        for prima, dopo in modifiche:
            conteggio[(prima, dopo)] = conteggio.get((prima, dopo), 0) + 1
        print(campo)
        for (prima, dopo), volte in sorted(conteggio.items()):
            print(f"  {prima} -> {dopo} ({volte})")

    print(f"Valori aggiornati: {totale}")


if __name__ == "__main__":
    main()
