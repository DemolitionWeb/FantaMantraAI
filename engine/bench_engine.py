from engine.role_engine import normalizza_ruoli


def crea_panchina(giocatori, titolari):
    titolari_ids = {
        assegnazione["giocatore"]["giocatore_id"]
        for assegnazione in titolari
    }

    disponibili = [
        giocatore
        for giocatore in giocatori
        if giocatore["disponibile"]
        and giocatore["score"] is not None
        and giocatore["giocatore_id"] not in titolari_ids
    ]

    disponibili.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    gruppi = (
        ("POR", {"POR"}, 1),
        ("DIF", {"DC", "DD", "DS", "E"}, 2),
        ("CEN", {"M", "C", "T", "W"}, 2),
        ("ATT", {"A", "PC"}, 2),
    )

    # Ogni giocatore occupa un solo posto in panchina, anche se i suoi
    # ruoli Mantra coprono più reparti (es. "E, M").
    usati = set()
    panchina = {}

    for nome_gruppo, ruoli_gruppo, posti in gruppi:
        scelti = []

        for giocatore in disponibili:
            if len(scelti) >= posti:
                break

            if giocatore["giocatore_id"] in usati:
                continue

            ruoli = normalizza_ruoli(giocatore["ruoli_mantra"])

            if ruoli_gruppo.intersection(ruoli):
                scelti.append(giocatore)
                usati.add(giocatore["giocatore_id"])

        panchina[nome_gruppo] = scelti

    return panchina