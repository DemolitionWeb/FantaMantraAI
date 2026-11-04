"""Difficoltà della prossima partita di una squadra (0 = facile, 100 = difficile).

Prima versione, volutamente semplice e spiegabile. Si basa sulla
classifica di football-data.org:

- 50% posizione in classifica dell'avversario (1° = 100, ultimo = 0);
- 25% attacco dell'avversario: gol fatti a partita rispetto al campionato;
- 25% difesa dell'avversario: gol subiti a partita (meno ne subisce,
  più è difficile segnargli);
- giocare in trasferta aggiunge 7,5 punti, in casa ne toglie 7,5.

La confidenza cresce con le partite giocate (10 partite = 100).
Senza classifica salvata la difficoltà resta non calcolata.
"""

from db.calendario import adesso_utc
from db.database import get_connection
from squadre import nome_canonico


PESO_POSIZIONE = 0.50
PESO_ATTACCO = 0.25
PESO_DIFESA = 0.25
FATTORE_CAMPO = 7.5


def _scala(valore, minimo, massimo):
    if massimo == minimo:
        return 50.0
    return 100 * (valore - minimo) / (massimo - minimo)


def _classifica():
    conn = get_connection()
    try:
        righe = conn.execute(
            """
            SELECT squadra, posizione, giocate, gol_fatti, gol_subiti, punti
            FROM classifica
            WHERE tipo = 'TOTAL' AND giocate > 0
            """
        ).fetchall()
    except Exception:
        righe = []
    finally:
        conn.close()

    return {
        nome_canonico(squadra): {
            "posizione": posizione, "giocate": giocate, "punti": punti,
            "gol_fatti": gol_fatti, "gol_subiti": gol_subiti,
            "attacco": gol_fatti / giocate, "difesa": gol_subiti / giocate,
        }
        for squadra, posizione, giocate, gol_fatti, gol_subiti, punti in righe
    }


def stima_difficolta(avversario, casa_trasferta, classifica):
    """Calcola difficoltà, confidenza e motivazione. None se mancano dati."""
    dati = classifica.get(avversario)
    if not dati or len(classifica) < 2:
        return None

    squadre = len(classifica)
    attacchi = [s["attacco"] for s in classifica.values()]
    difese = [s["difesa"] for s in classifica.values()]

    posizione = 100 * (squadre - dati["posizione"]) / (squadre - 1)
    attacco = _scala(dati["attacco"], min(attacchi), max(attacchi))
    # Meno gol subiti = difesa più forte = partita più difficile.
    difesa = 100 - _scala(dati["difesa"], min(difese), max(difese))

    punteggio = (
        PESO_POSIZIONE * posizione
        + PESO_ATTACCO * attacco
        + PESO_DIFESA * difesa
        + (FATTORE_CAMPO if casa_trasferta == "trasferta" else -FATTORE_CAMPO)
    )
    punteggio = round(max(0.0, min(100.0, punteggio)), 1)

    luogo = "in trasferta" if casa_trasferta == "trasferta" else "in casa"
    return {
        "difficulty_score": punteggio,
        "confidence": min(100, dati["giocate"] * 10),
        "componenti": {
            "posizione": round(posizione, 1),
            "attacco_avversario": round(attacco, 1),
            "difesa_avversario": round(difesa, 1),
        },
        "reason": (
            f"{avversario} è {dati['posizione']}° con {dati['punti']} punti, "
            f"{dati['gol_fatti']} gol fatti e {dati['gol_subiti']} subiti in "
            f"{dati['giocate']} partite; si gioca {luogo}."
        ),
    }


def calcola_match_difficulty(squadra, partita_id=None):
    squadra = nome_canonico(squadra)
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
            AND kickoff_utc >= ?
            AND (
                squadra_casa = ?
                OR squadra_trasferta = ?
            )
            ORDER BY kickoff_utc
            LIMIT 1
        """, (adesso_utc(), squadra, squadra))

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

    casa = nome_canonico(casa)
    trasferta = nome_canonico(trasferta)

    if squadra == casa:
        casa_trasferta = "casa"
        avversario = trasferta
    elif squadra == trasferta:
        casa_trasferta = "trasferta"
        avversario = casa
    else:
        return None

    risultato = {
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
            "manca la classifica dell'avversario."
        ),
    }

    stima = stima_difficolta(avversario, casa_trasferta, _classifica())
    if stima:
        risultato.update(stima)

    return risultato
