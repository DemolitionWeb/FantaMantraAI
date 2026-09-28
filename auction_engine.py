def crediti_rimanenti(budget_iniziale, spesa_totale):
    return budget_iniziale - spesa_totale


def offerta_massima(budget_iniziale, spesa_totale, crediti_da_conservare=1):
    rimanenti = crediti_rimanenti(budget_iniziale, spesa_totale)

    return max(0, rimanenti - crediti_da_conservare)


def percentuale_budget_speso(budget_iniziale, spesa_totale):
    if budget_iniziale <= 0:
        return 0

    return (spesa_totale / budget_iniziale) * 100