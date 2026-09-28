from engine.formations import FORMAZIONI
from engine.role_engine import ottimizza_formazione
from engine.tactical_engine import valuta_formazione


def valuta_formazioni(giocatori):
    risultati = []
    for nome, slot in FORMAZIONI.items():
        formazione = ottimizza_formazione(giocatori, slot)
        if formazione is None:
            continue
        risultati.append({
            "modulo": nome,
            "score_totale": formazione["score_totale"],
            "score_medio": formazione["score_medio"],
            **valuta_formazione(formazione["assegnazione"]),
            "assegnazione": formazione["assegnazione"],
        })
    risultati.sort(key=lambda x: (x["score_finale"] is not None, x["score_finale"] or -1),
                   reverse=True)
    return risultati

