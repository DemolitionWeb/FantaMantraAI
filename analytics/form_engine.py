from db.database import get_connection


def calcola_form(giocatore_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Le partite più recenti si ordinano per data di calcio d'inizio:
    # l'id della presenza riflette solo l'ordine di importazione.
    cursor.execute("""
        SELECT
            p.minuti,
            p.voto,
            p.gol,
            p.assist,
            p.titolare
        FROM presenze p
        LEFT JOIN partite pa ON pa.id = p.partita_id
        WHERE p.giocatore_id = ?
        ORDER BY pa.kickoff_utc DESC, p.id DESC
        LIMIT 5
    """, (giocatore_id,))

    presenze = cursor.fetchall()

    conn.close()

    if not presenze:
        return {
            "form_score": None,
            "media_voto_recenti": None,
            "media_minuti_recenti": None,
            "gol_recenti": 0,
            "assist_recenti": 0,
            "partite_recenti": 0,
            "confidenza": 0
        }

    voti = [
        float(p[1])
        for p in presenze
        if p[1] is not None and float(p[1]) > 0
    ]

    minuti = [
        float(p[0] or 0)
        for p in presenze
    ]

    gol = sum(int(p[2] or 0) for p in presenze)
    assist = sum(int(p[3] or 0) for p in presenze)

    media_minuti = (
        sum(minuti) / len(minuti)
        if minuti else 0
    )

    # Senza voti validi (solo "senza voto") la forma non è misurabile:
    # restituire 0 penalizzerebbe il giocatore per un dato mancante.
    if voti:
        media_voto = sum(voti) / len(voti)

        # Score provvisorio della forma.
        # 6.0 = 50 punti
        # 6.5 = 75 punti
        # 7.0 = 100 punti
        form_score = round(max(0, min(100, (media_voto - 5.0) * 50)), 1)
        media_voto = round(media_voto, 2)
    else:
        media_voto = None
        form_score = None

    # Più dati abbiamo, maggiore è la confidenza.
    confidenza = min(
        100,
        len(presenze) * 20
    )

    return {
        "form_score": form_score,
        "media_voto_recenti": media_voto,
        "media_minuti_recenti": round(media_minuti, 1),
        "gol_recenti": gol,
        "assist_recenti": assist,
        "partite_recenti": len(presenze),
        "confidenza": confidenza
    }