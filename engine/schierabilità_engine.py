from analytics.player_analytics import analizza_giocatore
from analytics.form_engine import calcola_form
from engine.starter_probability import calcola_starter_probability
from engine.match_difficult import calcola_match_difficulty


def calcola_schierabilita(giocatore_id):
    analytics = analizza_giocatore(giocatore_id)

    if not analytics:
        return None

    form = calcola_form(giocatore_id)

    starter = calcola_starter_probability(
        giocatore_id
    )

    squadra = analytics.get("squadra")

    match = None

    if squadra:
        match = calcola_match_difficulty(
            squadra
        )

    # -----------------------------
    # FATTORE TITOLARITÀ
    # -----------------------------

    if starter["starter_probability"] is not None:
        fattore_titolarita = (
            starter["starter_probability"]
        )
    else:
        fattore_titolarita = None

    # -----------------------------
    # FATTORE FORMA
    # -----------------------------

    fattore_forma = form["form_score"]

    # -----------------------------
    # FATTORE MINUTI
    # -----------------------------

    if starter["media_minuti"] > 0:
        fattore_minuti = min(
            100,
            starter["media_minuti"] / 90 * 100
        )
    else:
        fattore_minuti = None

    # -----------------------------
    # FATTORE MATCH
    # -----------------------------

    if match and match["difficulty_score"] is not None:
        fattore_match = (
            100 - match["difficulty_score"]
        )
    else:
        fattore_match = None

    # -----------------------------
    # DISPONIBILITÀ
    # -----------------------------

    # Per ora non abbiamo ancora
    # un vero Injury Engine.
    fattore_disponibilita = None

    # -----------------------------
    # COSTRUZIONE PUNTEGGIO
    # -----------------------------

    fattori = {
        "titolarita": fattore_titolarita,
        "forma": fattore_forma,
        "minuti": fattore_minuti,
        "match": fattore_match,
        "disponibilita": fattore_disponibilita,
    }

    fattori_validi = {
        nome: valore
        for nome, valore in fattori.items()
        if valore is not None
    }

    if not fattori_validi:
        score = None

    else:
        score = (
            sum(fattori_validi.values())
            / len(fattori_validi)
        )

    return {
        "giocatore_id": giocatore_id,
        "nome": analytics["nome"],
        "squadra": analytics["squadra"],
        "ruoli_mantra": analytics["ruoli_mantra"],
        "schierabilita": (
            round(score, 1)
            if score is not None
            else None
        ),
        "fattori": fattori,
        "data_confidence": min(
            starter["data_confidence"],
            form["confidenza"]
        ),
        "match": match,
    }