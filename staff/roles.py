"""Catalogo e istruzioni dello Staff Fantamantra AI."""

CATALOGO_STAFF = (
    {
        "nome": "Head Coach",
        "ruolo": "Coordina i pareri e formula la decisione finale.",
        "dati": "Contesto d'asta, budget e pareri degli specialisti.",
        "limite": "Dichiara i dati mancanti e rispetta l'offerta massima.",
        "stato": "Attivo",
        "nel_consulto": True,
    },
    {
        "nome": "Direttore sportivo",
        "ruolo": "Valuta l'acquisto rispetto a prezzo, rosa e strategia d'asta.",
        "dati": "Prezzo attuale, budget residuo e conteggi della rosa.",
        "limite": "Distingue i dati inseriti dalle valutazioni strategiche.",
        "stato": "Attivo",
        "nel_consulto": True,
    },
    {
        "nome": "Responsabile budget",
        "ruolo": "Tiene sotto controllo spesa, crediti residui e offerta massima.",
        "dati": "Valori calcolati dall'app tramite auction_engine.",
        "limite": "I calcoli dell'app sono vincolanti; non propone rilanci oltre il tetto.",
        "stato": "Attivo",
        "nel_consulto": True,
    },
    {
        "nome": "Analista Mantra",
        "ruolo": "Legge i ruoli e la composizione della rosa inseriti dall'utente.",
        "dati": "Conteggi dei ruoli Mantra presenti nell'app.",
        "limite": "Non assegna carenze assolute finché non esistono obiettivi di rosa configurati.",
        "stato": "Parziale",
        "nel_consulto": True,
    },
    {
        "nome": "Scout",
        "ruolo": "Esamina il giocatore all'asta sulla base delle informazioni disponibili.",
        "dati": "Nome, prezzo e ogni eventuale dato del giocatore passato al Coach.",
        "limite": "Il solo nome non dimostra rendimento, titolarità o stato fisico.",
        "stato": "Parziale",
        "nel_consulto": True,
    },
    {
        "nome": "Allenatore tattico Matchday",
        "ruolo": "Confronta moduli, titolari e copertura della panchina.",
        "dati": "Ruoli compatibili e presenze collegate ai giocatori della rosa.",
        "limite": "In pausa: lo storico disponibile non copre la rosa attuale.",
        "stato": "In pausa",
        "nel_consulto": False,
    },
    {
        "nome": "Analista disponibilità",
        "ruolo": "Riporta indisponibilità e rischi usando le fonti registrate.",
        "dati": "Record infortuni con fonte e aggiornamento, quando forniti al consulto.",
        "limite": "Non formula diagnosi e non presume che un dato assente significhi idoneità.",
        "stato": "In sviluppo",
        "nel_consulto": False,
    },
)

RUOLI_STAFF = tuple(
    {
        "nome": membro["nome"],
        "compito": membro["ruolo"],
        "limite": membro["limite"],
    }
    for membro in CATALOGO_STAFF
    if membro["nel_consulto"]
)


def costruisci_contesto_staff(contesto):
    """Aggiunge al contesto d'asta incarichi e limiti dei ruoli consultati."""
    righe = [
        "STAFF FANTAMANTRA — consulto coordinato",
        "I ruoli sono prospettive di analisi in una singola consultazione.",
        "Usa soltanto i dati riportati sotto; separa fatti e valutazioni.",
        "",
    ]

    for ruolo in RUOLI_STAFF:
        righe.append(f"{ruolo['nome']}: {ruolo['compito']}")
        righe.append(f"Limite: {ruolo['limite']}")

    righe.extend(
        [
            "",
            "DATI ASTA E ROSA",
            str(contesto).strip(),
            "",
            "FORMATO DELLA RISPOSTA",
            "1. Budget: prezzo attuale e offerta massima consentita.",
            "2. Mantra: cosa mostrano i conteggi; segnala se manca un obiettivo.",
            "3. Scout: dati disponibili e dati mancanti sul giocatore.",
            "4. Direttore sportivo: vantaggio e rischio dell'acquisto.",
            "5. Head Coach: comprare, rilanciare entro il limite, oppure passare.",
        ]
    )
    return "\n".join(righe)
