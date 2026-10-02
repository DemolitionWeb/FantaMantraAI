from db.presenze import normalizza_nome, normalizza_squadra, trova_giocatore as _trova_giocatore
from db.database import get_connection


def trova_giocatore_per_nome(nome):
    """Cerca un giocatore per nome completo, evitando risultati ambigui."""
    nome_normalizzato = " ".join(str(nome or "").strip().split()).casefold()
    if not nome_normalizzato:
        return None

    conn = get_connection()
    giocatori = conn.execute(
        """
        SELECT id, nome, squadra, ruoli_mantra
        FROM giocatori
        WHERE lower(trim(nome)) = ?
        ORDER BY nome
        """,
        (nome_normalizzato,),
    ).fetchall()
    conn.close()

    if len(giocatori) != 1:
        return None

    giocatore_id, nome_reale, squadra, ruoli = giocatori[0]
    return {
        "id": giocatore_id,
        "nome": nome_reale,
        "squadra": squadra,
        "ruoli_mantra": ruoli,
    }


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
