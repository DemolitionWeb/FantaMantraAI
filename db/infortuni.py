from datetime import datetime, timezone

from db.database import get_connection


def salva_infortunio(
    giocatore_id,
    fonte,
    fonte_id,
    tipo=None,
    descrizione=None,
    data_inizio=None,
    data_rientro=None,
    stato="attivo",
):
    conn = get_connection()
    cursor = conn.cursor()

    ultimo_aggiornamento = datetime.now(timezone.utc).isoformat()

    cursor.execute(
        """
        SELECT id
        FROM infortuni
        WHERE giocatore_id = ?
          AND fonte = ?
          AND fonte_id = ?
        """,
        (giocatore_id, fonte, fonte_id),
    )

    esistente = cursor.fetchone()

    if esistente:
        cursor.execute(
            """
            UPDATE infortuni
            SET tipo = ?,
                descrizione = ?,
                data_inizio = ?,
                data_rientro = ?,
                stato = ?,
                ultimo_aggiornamento = ?
            WHERE id = ?
            """,
            (
                tipo,
                descrizione,
                data_inizio,
                data_rientro,
                stato,
                ultimo_aggiornamento,
                esistente[0],
            ),
        )
    else:
        cursor.execute(
            """
            INSERT INTO infortuni (
                giocatore_id,
                fonte,
                fonte_id,
                tipo,
                descrizione,
                data_inizio,
                data_rientro,
                stato,
                ultimo_aggiornamento
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                giocatore_id,
                fonte,
                fonte_id,
                tipo,
                descrizione,
                data_inizio,
                data_rientro,
                stato,
                ultimo_aggiornamento,
            ),
        )

    conn.commit()
    conn.close()


def chiudi_infortuni_assenti(fonte, giocatori_ancora_infortunati):
    """Segna come risolti gli infortuni attivi non più presenti nella fonte.

    Va chiamata dopo un'importazione completa della lista infortuni: chi non
    compare più nella lista è tornato disponibile. Restituisce quanti
    infortuni sono stati chiusi.
    """
    ancora_attivi = list(set(giocatori_ancora_infortunati))
    ultimo_aggiornamento = datetime.now(timezone.utc).isoformat()

    segnaposti = ", ".join("?" for _ in ancora_attivi)
    filtro = (
        f"AND giocatore_id NOT IN ({segnaposti})" if ancora_attivi else ""
    )

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        UPDATE infortuni
        SET stato = 'risolto',
            ultimo_aggiornamento = ?
        WHERE fonte = ?
          AND stato = 'attivo'
          {filtro}
        """,
        (ultimo_aggiornamento, fonte, *ancora_attivi),
    )
    chiusi = cursor.rowcount
    conn.commit()
    conn.close()

    return chiusi