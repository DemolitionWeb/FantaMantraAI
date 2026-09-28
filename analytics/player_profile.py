from analytics.player_analytics import analizza_giocatore
from analytics.form_engine import calcola_form
from analytics.availability_engine import prossima_partita


def crea_profilo(giocatore_id):

    analytics = analizza_giocatore(giocatore_id)

    if not analytics:
        return None

    squadra = analytics.get("squadra")

    form = calcola_form(giocatore_id)

    partita = None

    if squadra:
        partita = prossima_partita(squadra)

    return {
        "analytics": analytics,
        "form": form,
        "prossima_partita": partita
    }