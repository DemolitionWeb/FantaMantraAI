from analytics.player_analytics import analizza_giocatore
from analytics.form_engine import calcola_form
from analytics.availability_engine import analizza_disponibilita
from engine.starter_probability import calcola_starter_probability
from engine.match_difficult import calcola_match_difficulty


def calcola_schierabilita(giocatore_id):
    analytics = analizza_giocatore(giocatore_id)
    form = calcola_form(giocatore_id)
    starter = calcola_starter_probability(giocatore_id)
    disponibilita = analizza_disponibilita(giocatore_id)

    squadra = analytics.get("squadra")

    match = None

    if squadra:
        match = calcola_match_difficulty(squadra)

    fattori = {}

    # 1. Titolarità
    starter_probability = starter.get("starter_probability")

    if starter_probability is not None:
        fattori["titolarita"] = starter_probability

    # 2. Forma
    form_score = form.get("form_score")

    if form_score is not None:
        fattori["forma"] = form_score

    # 3. Minuti medi
    media_minuti = starter.get("media_minuti", 0)

    if media_minuti > 0:
        fattori["minuti"] = min(
            100,
            (media_minuti / 90) * 100
        )

    # 4. Disponibilità
    if disponibilita.get("disponibile") is False:
        fattori["disponibilita"] = 0

    elif disponibilita.get("disponibile") is True:
        fattori["disponibilita"] = 100

    # 5. Difficoltà partita
    difficulty = None

    if match is not None:
        difficulty = match.get("difficulty_score")

    if difficulty is not None:
        fattori["match"] = 100 - difficulty

    # 6. Pesi V1
    pesi = {
        "titolarita": 0.30,
        "forma": 0.25,
        "minuti": 0.20,
        "disponibilita": 0.15,
        "match": 0.10,
    }

    numeratore = 0
    denominatore = 0

    for fattore, valore in fattori.items():
        peso = pesi.get(fattore, 0)

        numeratore += valore * peso
        denominatore += peso

    if denominatore > 0:
        score = numeratore / denominatore
        score = round(score, 1)
    else:
        score = None

    # Confidence
    confidence_values = [
        starter.get("data_confidence", 0),
        form.get("confidence", 0),
        disponibilita.get("confidence", 0),
    ]

    confidence = round(
        sum(confidence_values) / len(confidence_values),
        1,
    )

    # Fascia numerica
    if score is None:
        fascia = "DATI INSUFFICIENTI"
    elif score >= 85:
        fascia = "ECCELLENTE"
    elif score >= 70:
        fascia = "ALTA"
    elif score >= 55:
        fascia = "MEDIA"
    elif score >= 40:
        fascia = "BASSA"
    else:
        fascia = "MOLTO BASSA"

    return {
        "giocatore_id": giocatore_id,
        "nome": analytics.get("nome"),
        "squadra": analytics.get("squadra"),
        "score": score,
        "fascia": fascia,
        "fattori": fattori,
        "confidence": confidence,
        "disponibilita": disponibilita,
        "form": form,
        "starter_probability": starter,
        "match": match,
        "motivazioni": genera_motivazione({
        "fattori": fattori,
        "disponibilita": disponibilita,
        }),
    }

def genera_motivazione(risultato):
    motivazioni = []

    fattori = risultato.get("fattori", {})
    disponibilita = risultato.get(
        "disponibilita",
        {},
    )

    if disponibilita.get("infortunato"):
        motivazioni.append(
            "Giocatore attualmente presente "
            "nella lista infortuni."
        )
    else:
        motivazioni.append(
            "Nessun infortunio attivo registrato."
        )

    titolarita = fattori.get("titolarita")

    if titolarita is not None:
        if titolarita >= 80:
            motivazioni.append(
                "Elevata probabilità di titolarità."
            )
        elif titolarita >= 60:
            motivazioni.append(
                "Probabilità di titolarità intermedia."
            )
        else:
            motivazioni.append(
                "Probabilità di titolarità contenuta."
            )

    forma = fattori.get("forma")

    if forma is not None:
        if forma >= 75:
            motivazioni.append(
                "Forma recente positiva."
            )
        elif forma < 50:
            motivazioni.append(
                "Forma recente sotto il livello "
                "di riferimento."
            )

    minuti = fattori.get("minuti")

    if minuti is not None and minuti >= 80:
        motivazioni.append(
            "Buona continuità di minutaggio."
        )

    return motivazioni