def _media(formazione, chiave):
    valori = [float(a["giocatore"][chiave]) for a in formazione
              if isinstance(a.get("giocatore", {}).get(chiave), (int, float))]
    return round(sum(valori) / len(valori), 1) if valori else None


def calcola_equilibrio(formazione):
    ruoli = [a.get("slot", "").upper() for a in formazione]
    linee = (
        any(r in {"DC", "DD", "DS", "E"} for r in ruoli),
        any(r in {"M", "C", "T", "W"} for r in ruoli),
        any(r in {"A", "PC"} for r in ruoli),
    )
    return round(100 * sum(linee) / 3, 1) if formazione else 0


def calcola_affidabilita(formazione):
    return _media(formazione, "confidence")


def calcola_titolarita(formazione):
    return _media(formazione, "starter_probability")


def calcola_disponibilita(formazione):
    valori = [a.get("giocatore", {}).get("disponibile") for a in formazione]
    noti = [v for v in valori if isinstance(v, bool)]
    return round(100 * sum(noti) / len(noti), 1) if noti else None


def calcola_rischio(formazione):
    valore = calcola_disponibilita(formazione)
    return round(100 - valore, 1) if valore is not None else None


def valuta_formazione(formazione):
    if not formazione:
        return {"score_base": None, "equilibrio": 0, "affidabilita": None,
                "starter_probability_media": None, "disponibilita": None,
                "rischio": None, "score_finale": None}
    score = _media(formazione, "score")
    equilibrio = calcola_equilibrio(formazione)
    confidence = calcola_affidabilita(formazione)
    starter = calcola_titolarita(formazione)
    disponibilita = calcola_disponibilita(formazione)
    parti = [(v, p) for v, p in ((score, .35), (equilibrio, .20),
             (confidence, .20), (starter, .20), (disponibilita, .05)) if v is not None]
    peso = sum(p for _, p in parti)
    finale = round(sum(v*p for v, p in parti)/peso, 1) if peso else None
    return {"score_base": score, "equilibrio": equilibrio, "affidabilita": confidence,
            "starter_probability_media": starter, "disponibilita": disponibilita,
            "rischio": calcola_rischio(formazione), "score_finale": finale}

