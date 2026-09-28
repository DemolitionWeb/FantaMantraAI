from db.presenze import normalizza_nome, normalizza_squadra, trova_giocatore as _trova_giocatore
from db.database import get_connection


def trova_giocatore(nome, squadra):
    giocatore_id = _trova_giocatore(nome, squadra)
    if giocatore_id:
        conn = get_connection()
        giocatore = conn.execute(
            "SELECT id, nome, squadra FROM giocatori WHERE id = ?",
            (giocatore_id,),
        ).fetchone()
        conn.close()
        if giocatore:
            return {"id": giocatore[0], "nome": giocatore[1], "squadra": giocatore[2]}

    return None
