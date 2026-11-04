from datetime import datetime, timezone

from db.database import get_connection


COLONNE = (
    "stagione",
    "tipo",
    "squadra_id",
    "squadra",
    "squadra_nome_completo",
    "sigla",
    "posizione",
    "punti",
    "giocate",
    "vinte",
    "pareggiate",
    "perse",
    "gol_fatti",
    "gol_subiti",
    "differenza_reti",
    "giornata",
)


def salva_classifica(righe, fonte="football-data.org"):
    """Sostituisce la classifica salvata con quella appena scaricata.

    La classifica è un'istantanea: le righe vecchie vengono rimosse solo
    se ne arrivano di nuove, così un errore della fonte non svuota la
    tabella.
    """
    if not righe:
        return 0

    ultimo_aggiornamento = datetime.now(timezone.utc).isoformat()
    segnaposti = ", ".join("?" for _ in range(len(COLONNE) + 2))

    conn = get_connection()
    try:
        conn.execute("DELETE FROM classifica")
        conn.executemany(
            f"""
            INSERT INTO classifica ({", ".join(COLONNE)}, fonte, ultimo_aggiornamento)
            VALUES ({segnaposti})
            """,
            [
                tuple(riga.get(colonna) for colonna in COLONNE)
                + (fonte, ultimo_aggiornamento)
                for riga in righe
            ],
        )
        conn.commit()
    finally:
        conn.close()

    return len(righe)


def leggi_classifica(tipo="TOTAL"):
    """Classifica ordinata per posizione, come lista di dizionari."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            f"""
            SELECT {", ".join(COLONNE)}, ultimo_aggiornamento
            FROM classifica
            WHERE tipo = ?
            ORDER BY posizione
            """,
            (tipo,),
        )
        nomi = [colonna[0] for colonna in cursor.description]
        return [dict(zip(nomi, riga)) for riga in cursor.fetchall()]
    finally:
        conn.close()
