import unicodedata
import re
import sqlite3

from db.database import get_connection, salva_player_source


def normalizza_nome(nome):
    if not nome:
        return ""

    nome = str(nome).strip().lower()

    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(
        carattere
        for carattere in nome
        if not unicodedata.combining(carattere)
    )

    # Le fonti usano forme diverse ("J. Bijol", "J-Bijol", "J Bijol").
    # La punteggiatura non identifica il giocatore e non deve impedire il match.
    nome = re.sub(r"[^a-z0-9]+", " ", nome)
    return " ".join(nome.split())


def normalizza_squadra(squadra):
    """Normalizza il nome della squadra senza fare match troppo permissivi."""
    squadra = normalizza_nome(squadra)
    squadra = re.sub(r"\b(fc|ac|ss|calcio)\b", "", squadra)
    return " ".join(squadra.split())


def _cognome(nome):
    parole = normalizza_nome(nome).replace(".", " ").split()
    return parole[-1] if parole else ""


def _trova_source(cursor, fonte_id):
    """Legge entrambi i registri storici degli ID esterni."""
    if not fonte_id:
        return None
    valore = str(fonte_id)
    cursor.execute(
        """
        SELECT giocatore_id FROM player_sources
        WHERE lower(fonte) = 'bbs' AND fonte_id = ?
        """,
        (valore,),
    )
    risultato = cursor.fetchone()
    if risultato:
        return risultato[0]

    # giocatori_fonti è il registro più vecchio; tenerlo compatibile evita
    # di perdere collegamenti già creati dalle prime importazioni.
    try:
        cursor.execute(
            """
            SELECT giocatore_id FROM giocatori_fonti
            WHERE lower(fonte) = 'bbs' AND fonte_id = ?
            """,
            (valore,),
        )
        risultato = cursor.fetchone()
        return risultato[0] if risultato else None
    except sqlite3.OperationalError:
        # Database creati prima della migrazione: il registro canonico sopra
        # resta sufficiente per continuare a importare i dati.
        return None


def trova_giocatore(nome, squadra, fonte_id=None):
    """Collega un giocatore a un solo ID interno, in ordine di affidabilità.

    L'ID della fonte è la chiave più forte: nome e squadra possono cambiare
    formato o aggiornarsi dopo un trasferimento. Il cognome viene usato solo
    quando è univoco nella stessa squadra.
    """
    nome_normalizzato = normalizza_nome(nome)
    squadra_normalizzata = normalizza_squadra(squadra)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT g.id, g.nome, g.squadra,
               CASE WHEN r.giocatore_id IS NULL THEN 0 ELSE 1 END
        FROM giocatori g
        LEFT JOIN rosa r ON r.giocatore_id = g.id
        """
    )
    righe = cursor.fetchall()

    # 1. Mapping esplicito della fonte, prima di qualsiasi euristica.
    source_id = _trova_source(cursor, fonte_id)
    if source_id and any(r[0] == source_id for r in righe):
        conn.close()
        return source_id

    def squadra_coincide(riga):
        return normalizza_squadra(riga[2]) == squadra_normalizzata

    exact_rosa = [
        r for r in righe
        if r[3] and squadra_coincide(r)
        and normalizza_nome(r[1]) == nome_normalizzato
    ]
    if len(exact_rosa) == 1:
        conn.close()
        return exact_rosa[0][0]
    if len(exact_rosa) > 1:
        conn.close()
        return None

    cognome = _cognome(nome)
    if len(cognome) >= 3:
        cognome_rosa = [
            r for r in righe
            if r[3] and squadra_coincide(r) and _cognome(r[1]) == cognome
        ]
        if len(cognome_rosa) == 1:
            conn.close()
            return cognome_rosa[0][0]
        if len(cognome_rosa) > 1:
            conn.close()
            return None

    if fonte_id:
        cursor.execute(
            "SELECT giocatore_id FROM player_sources WHERE fonte = ? AND fonte_id = ?",
            ("BBS", str(fonte_id)),
        )
        source = cursor.fetchone()
        if source:
            source_row = next((r for r in righe if r[0] == source[0]), None)
            if source_row and squadra_coincide(source_row):
                conn.close()
                return source[0]

    exact = [r for r in righe if squadra_coincide(r)
             and normalizza_nome(r[1]) == nome_normalizzato]
    if len(exact) == 1:
        conn.close()
        return exact[0][0]

    cognome_match = [r for r in righe if squadra_coincide(r)
                     and len(cognome) >= 3 and _cognome(r[1]) == cognome]
    conn.close()
    return cognome_match[0][0] if len(cognome_match) == 1 else None

def registra_giocatore_bbs(giocatore):
    nome = giocatore.get("name")
    squadra = giocatore.get("team_name")
    fonte_id = giocatore.get("id")

    if not nome or not squadra or not fonte_id:
        return None

    giocatore_id = f"{nome}-{squadra}"

    dati = {
        "id": giocatore_id,
        "nome": nome,
        "squadra": squadra,
        "ruoli_mantra": None,
        "posizione_generica": giocatore.get("position"),
        "numero_maglia": giocatore.get("jersey_number"),
        "fonte_id": fonte_id,
        "fonte": "BBS",
        "ultimo_aggiornamento": "2026-09-24",
    }

    from db.database import salva_giocatori

    salva_giocatori([dati])

    return giocatore_id


def trasforma_statistiche_partita(
    match_id,
    partita,
    lineups,
    statistiche
):
    presenze = []

    # -----------------------------------------
    # SQUADRE UFFICIALI DELLA PARTITA
    # -----------------------------------------

    dati_partita = partita.get("data", {})

    home = dati_partita.get("home", {})
    away = dati_partita.get("away", {})

    team_ids_validi = {
        home.get("id"),
        away.get("id"),
    }

    team_ids_validi.discard(None)

    # -----------------------------------------
    # GIOCATORI PRESENTI NELLE LINEUP
    # -----------------------------------------

    giocatori_lineup = {}

    for squadra in ["home", "away"]:
        for giocatore in lineups.get("data", {}).get(squadra, []):

            player_id = giocatore.get("player_id")

            if not player_id:
                continue

            giocatori_lineup[player_id] = giocatore

    # -----------------------------------------
    # STATISTICHE
    # -----------------------------------------

    giocatori_stats = statistiche.get(
        "data", {}
    ).get("players", [])

    for giocatore in giocatori_stats:

        player_id = giocatore.get("id")

        # Il giocatore deve essere presente
        # nella lineup della partita
        if player_id not in giocatori_lineup:
            continue

        # Il giocatore deve appartenere
        # a una delle due squadre della partita
        team_id = giocatore.get("team_id")

        if team_id not in team_ids_validi:
            continue

        nome = giocatore.get("name")

        if not nome:
            continue

        lineup = giocatori_lineup[player_id]

        stats = giocatore.get("stats", {})

        # -----------------------------------------
        # SQUADRA DAL MATCH
        # -----------------------------------------

        if team_id == home.get("id"):
            squadra = home.get("name")

        elif team_id == away.get("id"):
            squadra = away.get("name")

        else:
            continue

        # -----------------------------------------
        # COLLEGAMENTO AL NOSTRO DATABASE
        # -----------------------------------------

        giocatore_id = trova_giocatore(
            nome,
            squadra,
            fonte_id=player_id,
        )

        if not giocatore_id:

            giocatore_id = registra_giocatore_bbs({
                "id": player_id,
                "name": nome,
                "team_name": squadra,
                "position": giocatore.get("position"),
                "jersey_number": giocatore.get("jersey_number"),
            })

        if not giocatore_id:
            continue

        # Conserva l'identificativo BBS anche quando il nome
        # della fonte differisce da quello usato nella rosa.
        salva_player_source(
            giocatore_id,
            "BBS",
            str(player_id),
        )

        # -----------------------------------------
        # LETTURA STATISTICHE
        # -----------------------------------------

        def valore(nome_statistica, default=0):

            dato = stats.get(nome_statistica)

            if isinstance(dato, dict):
                return dato.get(
                    "value",
                    default
                )

            return (
                dato
                if dato is not None
                else default
            )

        presenza = {
            "giocatore_id": giocatore_id,
            "partita_id": match_id,

            "titolare": (
                1
                if lineup.get("starter")
                else 0
            ),

            "minuti": int(
                valore("minutes", 0)
            ),

            "posizione": (
                lineup.get("position")
                or giocatore.get("position")
            ),

            "numero_maglia": (
                giocatore.get("jersey_number")
            ),

            "voto": float(
                valore("rating", 0)
            ),

            "gol": int(
                valore("goals", 0)
            ),

            "assist": int(
                valore("assists", 0)
            ),

            "ammonizioni": int(
                valore("yellow_cards", 0)
            ),

            "espulsioni": int(
                valore("red_cards", 0)
            ),
        }

        presenze.append(presenza)

    return presenze
