from db.database import get_connection


def calcola_match_difficulty(squadra, partita_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if partita_id:
        cursor.execute("""
            SELECT
                id,
                squadra_casa,
                squadra_trasferta,
                kickoff_utc,
                stato
            FROM partite
            WHERE id = ?
        """, (partita_id,))
    else:
        cursor.execute("""
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
            ORDER BY kickoff_utc
            LIMIT 1
        """, (squadra, squadra))

    partita = cursor.fetchone()

    conn.close()

    if not partita:
        return None

    (
        match_id,
        casa,
        trasferta,
        kickoff,
        stato
    ) = partita

    if squadra == casa:
        casa_trasferta = "casa"
        avversario = trasferta
    elif squadra == trasferta:
        casa_trasferta = "trasferta"
        avversario = casa
    else:
        return None

    # Versione iniziale neutrale:
    # senza dati sulla forza delle squadre,
    # non inventiamo una difficoltà.
    return {
        "match_id": match_id,
        "squadra": squadra,
        "avversario": avversario,
        "casa_trasferta": casa_trasferta,
        "kickoff": kickoff,
        "stato": stato,
        "difficulty_score": None,
        "confidence": 0,
        "reason": (
            "Difficoltà non ancora calcolabile: "
            "mancano dati strutturati sulla forza "
            "dell'avversario."
        )
    }