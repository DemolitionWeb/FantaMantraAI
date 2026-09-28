from engine.bench_engine import crea_panchina
from db.database import get_connection
from engine.schierabilita_engine import calcola_schierabilita
from engine.formation_optimizer import valuta_formazioni


def carica_rosa():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.id, g.nome, g.squadra, g.ruoli_mantra, g.posizione_generica
        FROM rosa r JOIN giocatori g ON g.id = r.giocatore_id ORDER BY g.nome
    """)
    giocatori = cursor.fetchall()
    conn.close()
    return giocatori


def analizza_rosa():
    risultati = []
    for record in carica_rosa():
        gid, nome, squadra, ruoli, posizione = record
        sch = calcola_schierabilita(gid)
        disp = sch["disponibilita"]
        starter = sch.get("starter_probability") or {}
        risultati.append({
            "giocatore_id": gid, "nome": nome, "squadra": squadra,
            "ruoli_mantra": ruoli, "posizione_generica": posizione,
            "fattori": sch.get("fattori", {}),
            "score": (sch["score"] if any(k in sch.get("fattori", {})
                      for k in ("titolarita", "forma", "minuti")) else None), "fascia": sch["fascia"],
            "confidence": sch["confidence"],
            "starter_probability": starter.get("starter_probability"),
            "partite_analizzate": starter.get("partite_analizzate", 0),
            "disponibile": disp.get("disponibile"),
            "infortunato": disp.get("infortunato"),
            "motivazioni": sch.get("motivazioni", []),
        })
    return risultati


def ordina_giocatori(risultati):
    return sorted(risultati,
                  key=lambda x: (x["score"] is not None, x["score"] or -1),
                  reverse=True)


def crea_matchday():
    rosa = analizza_rosa()
    ordinata = ordina_giocatori(rosa)
    formazioni = valuta_formazioni(rosa)
    migliore = formazioni[0] if formazioni else None
    panchina = crea_panchina(rosa, migliore["assegnazione"]) if migliore else {}
    return {"giocatori": ordinata, "numero_giocatori": len(ordinata),
            "formazioni": formazioni, "migliore": migliore, "panchina": panchina}


def genera_matchday_report():
    risultato = crea_matchday()
    formazioni = risultato["formazioni"]
    if not formazioni:
        return {"stato": "non_completamente_analizzabile",
                "giocatori_analizzati": risultato["numero_giocatori"],
                "formazione": None, "panchina": {}, "alternative": [],
                "metriche": {"copertura_ruoli_panchina": 0.0,
                             "motivo": "Nessun modulo completabile con ruoli e dati disponibili."}}
    migliore = formazioni[0]
    panchina = risultato["panchina"]
    gruppi = ("POR", "DIF", "CEN", "ATT")
    copertura = round(100 * sum(bool(panchina.get(g)) for g in gruppi) / len(gruppi), 1)
    return {"stato": "analizzato",
            "giocatori_analizzati": risultato["numero_giocatori"],
            "formazione": migliore, "panchina": panchina,
            "alternative": formazioni[1:4],
            "metriche": {
                "confidence_media": migliore["affidabilita"],
                "starter_probability_media": migliore["starter_probability_media"],
                "disponibilita_percentuale": migliore["disponibilita"],
                "rischio_indisponibilita_percentuale": migliore["rischio"],
                "copertura_ruoli_panchina": copertura,
            }}


