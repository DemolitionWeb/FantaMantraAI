"""Client per l'API di football-data.org (v4).

Piano gratuito: Serie A inclusa, massimo 10 richieste al minuto.
La chiave si ottiene registrandosi su
https://www.football-data.org/client/register e va messa nel file .env
come FOOTBALL_DATA_API_TOKEN.
"""

import requests

import config
from squadre import nome_canonico


BASE_URL = "https://api.football-data.org/v4"
SERIE_A = "SA"


def _headers():
    token = config.FOOTBALL_DATA_API_TOKEN
    if not token:
        raise ValueError(
            "FOOTBALL_DATA_API_TOKEN non configurata: aggiungila al file .env."
        )
    return {"X-Auth-Token": token}


def _get(path, params=None):
    response = requests.get(
        f"{BASE_URL}{path}",
        headers=_headers(),
        params=params,
        timeout=15,
    )

    if response.status_code == 429:
        raise RuntimeError(
            "Limite di richieste football-data.org superato "
            "(piano gratuito: 10 al minuto). Riprova tra un minuto."
        )

    response.raise_for_status()
    return response.json()


def get_classifica(competizione=SERIE_A):
    """Classifica totale, casa e trasferta della competizione."""
    return _get(f"/competitions/{competizione}/standings")


def get_partite(competizione=SERIE_A, giornata=None, stato=None):
    """Partite della competizione, filtrabili per giornata o stato
    (es. "SCHEDULED", "FINISHED")."""
    params = {}
    if giornata is not None:
        params["matchday"] = giornata
    if stato:
        params["status"] = stato
    return _get(f"/competitions/{competizione}/matches", params or None)


def nome_squadra(squadra):
    """Nome allineato al listone: "Como 1907" -> "Como",
    "Venezia FC" -> "Venezia"."""
    return nome_canonico(squadra.get("shortName") or squadra.get("name") or "")


def trasforma_classifica(risposta):
    """Converte la risposta /standings in righe per la tabella classifica.

    Una riga per squadra e per tipo di classifica (TOTAL, HOME, AWAY).
    Come nome squadra si usa lo shortName ("Inter", "Milan", ...), più
    vicino ai nomi del listone rispetto al nome completo.
    """
    stagione = (risposta.get("season") or {}).get("startDate", "")[:4] or None
    giornata = (risposta.get("season") or {}).get("currentMatchday")
    righe = []

    for blocco in risposta.get("standings", []):
        tipo = blocco.get("type")
        for riga in blocco.get("table", []):
            squadra = riga.get("team") or {}
            righe.append({
                "stagione": stagione,
                "tipo": tipo,
                "squadra_id": squadra.get("id"),
                "squadra": nome_squadra(squadra),
                "squadra_nome_completo": squadra.get("name"),
                "sigla": squadra.get("tla"),
                "posizione": riga.get("position"),
                "punti": riga.get("points"),
                "giocate": riga.get("playedGames"),
                "vinte": riga.get("won"),
                "pareggiate": riga.get("draw"),
                "perse": riga.get("lost"),
                "gol_fatti": riga.get("goalsFor"),
                "gol_subiti": riga.get("goalsAgainst"),
                "differenza_reti": riga.get("goalDifference"),
                "giornata": giornata,
            })

    return righe
