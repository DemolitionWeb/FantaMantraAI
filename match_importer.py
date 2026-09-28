from db.database import salva_partite


def normalizza_partita(partita):
    """
    Trasforma una partita proveniente da una fonte esterna
    nel formato interno di Fantamantra.
    """

    return {
        "id": partita.get("id"),
        "campionato": partita.get("league"),
        "giornata": partita.get("round"),
        "squadra_casa": partita.get("home_team"),
        "squadra_trasferta": partita.get("away_team"),
        "kickoff_utc": partita.get("kickoff"),
        "stato": partita.get("status"),
        "gol_casa": partita.get("home_score"),
        "gol_trasferta": partita.get("away_score"),
    }


def importa_partite(partite):
    partite_normalizzate = []

    for partita in partite:
        partita_normalizzata = normalizza_partita(partita)

        if not partita_normalizzata["id"]:
            continue

        partite_normalizzate.append(partita_normalizzata)

    salva_partite(partite_normalizzate)

    return len(partite_normalizzate)