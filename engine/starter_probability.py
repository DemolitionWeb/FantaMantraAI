from db.database import get_connection


def calcola_starter_probability(giocatore_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) AS partite,
            SUM(CASE WHEN titolare = 1 THEN 1 ELSE 0 END) AS titolari,
            AVG(minuti) AS media_minuti
        FROM presenze
        WHERE giocatore_id = ?
    """, (giocatore_id,))

    risultato = cursor.fetchone()

    conn.close()

    partite = risultato[0] or 0
    titolari = risultato[1] or 0
    media_minuti = float(risultato[2] or 0)

    # Nessun dato storico disponibile.
    if partite == 0:
        return {
            "starter_probability": None,
            "data_confidence": 0,
            "partite_analizzate": 0,
            "percentuale_titolarita": None,
            "media_minuti": 0,
        }

    percentuale_titolarita = (
        titolari / partite
    ) * 100

    # Componente principale:
    # frequenza con cui il giocatore è partito titolare.
    starter_probability = percentuale_titolarita

    # La confidenza cresce con il numero di partite osservate.
    data_confidence = min(
        100,
        partite * 20
    )

    return {
        "starter_probability": round(
            starter_probability,
            1
        ),
        "data_confidence": data_confidence,
        "partite_analizzate": partite,
        "percentuale_titolarita": round(
            percentuale_titolarita,
            1
        ),
        "media_minuti": round(
            media_minuti,
            1
        ),
    }