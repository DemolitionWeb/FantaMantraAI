def crediti_rimanenti(budget_iniziale, spesa_totale):
    return budget_iniziale - spesa_totale


def offerta_massima(
    budget_iniziale,
    spesa_totale,
    crediti_da_conservare=1,
    posti_da_riempire=None,
):
    """Offerta massima per il giocatore in asta.

    Se è noto quanti posti restano liberi in rosa, va conservato almeno
    1 credito per ciascun posto successivo a quello in asta, altrimenti
    la rosa non può essere completata.
    """
    rimanenti = crediti_rimanenti(budget_iniziale, spesa_totale)

    if posti_da_riempire is not None:
        if posti_da_riempire <= 0:
            return 0
        crediti_da_conservare = posti_da_riempire - 1

    return max(0, rimanenti - crediti_da_conservare)


def percentuale_budget_speso(budget_iniziale, spesa_totale):
    if budget_iniziale <= 0:
        return 0

    return (spesa_totale / budget_iniziale) * 100