import re


def normalizza_ruoli(ruoli):
    if not ruoli:
        return []
    return [r for r in re.split(r"[,/;|\s]+", str(ruoli).strip().upper()) if r]


def giocatore_compatibile(ruoli_giocatore, ruolo_slot):
    return ruolo_slot.upper() in normalizza_ruoli(ruoli_giocatore)


def costruisci_candidati(giocatori, ruolo_slot):
    return [g for g in giocatori if g.get("disponibile") and g.get("score") is not None
            and giocatore_compatibile(g.get("ruoli_mantra"), ruolo_slot)]


def ottimizza_formazione(giocatori, slot):
    migliori, miglior_score = None, float("-inf")
    candidati = [costruisci_candidati(giocatori, r) for r in slot]
    if not slot or any(not gruppo for gruppo in candidati):
        return None

    def cerca(i, usati, assegnazione, totale):
        nonlocal migliori, miglior_score
        if i == len(slot):
            if totale > miglior_score:
                migliori, miglior_score = assegnazione.copy(), totale
            return
        for giocatore in candidati[i]:
            gid = giocatore["giocatore_id"]
            if gid in usati:
                continue
            usati.add(gid)
            assegnazione.append({"slot": slot[i], "giocatore": giocatore})
            cerca(i + 1, usati, assegnazione, totale + giocatore["score"])
            assegnazione.pop()
            usati.remove(gid)

    cerca(0, set(), [], 0)
    if migliori is None:
        return None
    return {"slot": slot, "assegnazione": migliori,
            "score_totale": round(miglior_score, 1),
            "score_medio": round(miglior_score / len(slot), 1)}

