from db.database import get_connection


def prossima_partita(squadra):
    """Restituisce la prossima partita programmata della squadra."""
    if not squadra:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            squadra_casa,
            squadra_trasferta,
            kickoff_utc,
            stato
        FROM partite
        WHERE stato = 'scheduled'
          AND (
              squadra_casa = ?
              OR squadra_trasferta = ?
          )
        ORDER BY kickoff_utc ASC
        LIMIT 1
        """,
        (squadra, squadra),
    )

    partita = cursor.fetchone()
    conn.close()

    if not partita:
        return None

    partita_id, casa, trasferta, kickoff, stato = partita

    return {
        "partita_id": partita_id,
        "casa": casa,
        "trasferta": trasferta,
        "kickoff": kickoff,
        "stato": stato,
    }


def analizza_disponibilita(giocatore_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            nome,
            squadra
        FROM giocatori
        WHERE id = ?
        """,
        (giocatore_id,),
    )

    giocatore = cursor.fetchone()

    if not giocatore:
        conn.close()

        return {
            "giocatore_id": giocatore_id,
            "nome": None,
            "squadra": None,
            "disponibile": None,
            "infortunato": None,
            "tipo_infortunio": None,
            "data_rientro": None,
            "confidence": 0,
            "fonte": None,
        }

    nome, squadra = giocatore

    cursor.execute(
        """
        SELECT
            tipo,
            descrizione,
            data_inizio,
            data_rientro,
            stato,
            fonte
        FROM infortuni
        WHERE giocatore_id = ?
          AND stato = 'attivo'
        ORDER BY ultimo_aggiornamento DESC
        LIMIT 1
        """,
        (giocatore_id,),
    )

    infortunio = cursor.fetchone()

    conn.close()

    if infortunio:
        (
            tipo,
            descrizione,
            data_inizio,
            data_rientro,
            stato,
            fonte,
        ) = infortunio

        return {
            "giocatore_id": giocatore_id,
            "nome": nome,
            "squadra": squadra,
            "disponibile": False,
            "infortunato": True,
            "tipo_infortunio": tipo,
            "descrizione": descrizione,
            "data_inizio": data_inizio,
            "data_rientro": data_rientro,
            "confidence": 90,
            "fonte": fonte,
        }

    return {
        "giocatore_id": giocatore_id,
        "nome": nome,
        "squadra": squadra,
        "disponibile": True,
        "infortunato": False,
        "tipo_infortunio": None,
        "descrizione": None,
        "data_inizio": None,
        "data_rientro": None,
        "confidence": 90,
        "fonte": "database_infortuni",
    }
