from db.database import get_connection


def analizza_giocatore(giocatore_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            g.id,
            g.nome,
            g.squadra,
            g.ruoli_mantra,
            g.posizione_generica,
            r.quotazione_attuale,
            r.fvm,
            r.media_voto,
            r.fanta_media,
            r.partite_giocate
        FROM giocatori g
        LEFT JOIN rosa r
            ON g.id = r.giocatore_id
        WHERE g.id = ?
    """, (giocatore_id,))

    giocatore = cursor.fetchone()

    if not giocatore:
        conn.close()
        return None

    cursor.execute("""
        SELECT
            p.minuti,
            p.titolare,
            p.voto,
            p.gol,
            p.assist,
            p.ammonizioni,
            p.espulsioni
        FROM presenze p
        WHERE p.giocatore_id = ?
        ORDER BY p.id DESC
    """, (giocatore_id,))

    presenze = cursor.fetchall()

    conn.close()

    nome = giocatore[1]

    if not presenze:
        return {
            "id": giocatore[0],
            "nome": nome,
            "squadra": giocatore[2],
            "ruoli_mantra": giocatore[3],
            "presenze": 0,
            "titolari": 0,
            "titolarita": 0,
            "media_minuti": 0,
            "media_voto": giocatore[7] or 0,
            "gol": 0,
            "assist": 0,
            "quotazione": giocatore[5],
            "fvm": giocatore[6],
            "media_voto_rosa": giocatore[7],
            "fanta_media": giocatore[8],
    }

    totale = len(presenze)

    titolari = sum(
        1 for p in presenze
        if p[1] == 1
    )

    minuti = sum(
        p[0] or 0 for p in presenze
    )

    voti = [
        p[2] for p in presenze
        if p[2] is not None and p[2] > 0
    ]

    gol = sum(
        p[3] or 0 for p in presenze
    )

    assist = sum(
        p[4] or 0 for p in presenze
    )

    media_voto = (
        sum(voti) / len(voti)
        if voti else 0
    )

    media_minuti = minuti / totale

    percentuale_titolarita = (
        titolari / totale * 100
    )

    return {
        "id": giocatore[0],
        "nome": nome,
        "squadra": giocatore[2],
        "ruoli_mantra": giocatore[3],
        "presenze": totale,
        "titolari": titolari,
        "titolarita": round(percentuale_titolarita, 1),
        "media_minuti": round(media_minuti, 1),
        "media_voto": round(media_voto, 2),
        "gol": gol,
        "assist": assist,
        "quotazione": giocatore[5],
        "fvm": giocatore[6],
        "media_voto_rosa": giocatore[7],
        "fanta_media": giocatore[8],
    }