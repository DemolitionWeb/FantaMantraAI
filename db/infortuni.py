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