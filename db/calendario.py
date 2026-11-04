"""Calendario di Serie A da football-data.org nella tabella partite.

Le partite già salvate da BigBalls (stessa data e stesse squadre)
vengono aggiornate mantenendo il loro ID, così le presenze collegate non
si perdono. Le altre vengono inserite con ID "FD-<id football-data>".
"""

from datetime import datetime, timezone

from db.database import get_connection
from squadre import nome_canonico


STATI = {
    "SCHEDULED": "scheduled",
    "TIMED": "scheduled",
    "IN_PLAY": "live",
    "PAUSED": "live",
    "FINISHED": "finished",
    "AWARDED": "finished",
    "POSTPONED": "postponed",
    "SUSPENDED": "suspended",
    "CANCELLED": "cancelled",
}


def adesso_utc():
    """Istante attuale nel formato dei kickoff salvati, per i confronti."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def trasforma_partite(risposta):
    """Converte la risposta /matches di football-data in righe partite."""
    partite = []

    for partita in risposta.get("matches", []):
        casa = partita.get("homeTeam") or {}
        trasferta = partita.get("awayTeam") or {}
        punteggio = (partita.get("score") or {}).get("fullTime") or {}
        partite.append({
            "id": f"FD-{partita.get('id')}",
            "campionato": "Serie A",
            "giornata": partita.get("matchday"),
            "squadra_casa": nome_canonico(casa.get("shortName") or casa.get("name")),
            "squadra_trasferta": nome_canonico(
                trasferta.get("shortName") or trasferta.get("name")
            ),
            "kickoff_utc": partita.get("utcDate"),
            "stato": STATI.get(partita.get("status"), str(partita.get("status", "")).lower()),
            "gol_casa": punteggio.get("home"),
            "gol_trasferta": punteggio.get("away"),
        })

    return partite


def salva_calendario(partite):
    """Inserisce o aggiorna le partite. Restituisce (nuove, aggiornate)."""
    nuove = aggiornate = 0
    conn = get_connection()

    try:
        for partita in partite:
            if not partita["kickoff_utc"] or not partita["squadra_casa"]:
                continue

            esistente = conn.execute(
                """
                SELECT id FROM partite
                WHERE id = ?
                   OR (substr(kickoff_utc, 1, 10) = substr(?, 1, 10)
                       AND squadra_casa = ? AND squadra_trasferta = ?)
                ORDER BY id = ? DESC
                LIMIT 1
                """,
                (partita["id"], partita["kickoff_utc"], partita["squadra_casa"],
                 partita["squadra_trasferta"], partita["id"]),
            ).fetchone()

            valori = (
                partita["campionato"], partita["giornata"],
                partita["squadra_casa"], partita["squadra_trasferta"],
                partita["kickoff_utc"], partita["stato"],
                partita["gol_casa"], partita["gol_trasferta"],
            )

            if esistente:
                conn.execute(
                    """
                    UPDATE partite
                    SET campionato = ?, giornata = ?, squadra_casa = ?,
                        squadra_trasferta = ?, kickoff_utc = ?, stato = ?,
                        gol_casa = ?, gol_trasferta = ?
                    WHERE id = ?
                    """,
                    (*valori, esistente[0]),
                )
                aggiornate += 1
            else:
                conn.execute(
                    """
                    INSERT INTO partite (campionato, giornata, squadra_casa,
                        squadra_trasferta, kickoff_utc, stato, gol_casa,
                        gol_trasferta, id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (*valori, partita["id"]),
                )
                nuove += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return nuove, aggiornate
