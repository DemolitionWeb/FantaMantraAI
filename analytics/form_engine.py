from db.database import get_connection


def calcola_form(giocatore_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            minuti,
            voto,
            gol,
            assist,
            titolare
        FROM presenze
        WHERE giocatore_id = ?
        ORDER BY id DESC
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

    media_voto = (
        sum(voti) / len(voti)
        if voti else 0
    )

    media_minuti = (
        sum(minuti) / len(minuti)
        if minuti else 0
    )

    # Score provvisorio della forma.
    # 6.0 = 50 punti
    # 6.5 = 75 punti
    # 7.0 = 100 punti
    form_score = max(
        0,
        min(
            100,
            (media_voto - 5.0) * 50
        )
    )

    # Più dati abbiamo, maggiore è la confidenza.
    confidenza = min(
        100,
        len(presenze) * 20
    )

    return {
        "form_score": round(form_score, 1),
        "media_voto_recenti": round(media_voto, 2),
        "media_minuti_recenti": round(media_minuti, 1),
        "gol_recenti": gol,
        "assist_recenti": assist,
        "partite_recenti": len(presenze),
        "confidenza": confidenza
    }