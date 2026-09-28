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

    portieri = []
    difensori = []
    centrocampisti = []
    attaccanti = []

    for giocatore in disponibili:
        ruoli = normalizza_ruoli(
            giocatore["ruoli_mantra"]
        )

        if "POR" in ruoli:
            portieri.append(giocatore)

        if any(
            ruolo in ruoli
            for ruolo in ["DC", "DD", "DS", "E"]
        ):
            difensori.append(giocatore)

        if any(
            ruolo in ruoli
            for ruolo in ["M", "C", "T", "W"]
        ):
            centrocampisti.append(giocatore)

        if any(
            ruolo in ruoli
            for ruolo in ["A", "PC"]
        ):
            attaccanti.append(giocatore)

    return {
        "POR": portieri[:1],
        "DIF": difensori[:2],
        "CEN": centrocampisti[:2],
        "ATT": attaccanti[:2],
    }