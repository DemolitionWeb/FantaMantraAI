# Fantamantra AI

Fantamantra AI è un assistente per il Fantacalcio Mantra. Il progetto nasce
per aiutare il fantallenatore durante l'asta e, in una fase successiva, durante
la gestione della giornata.

## Obiettivo

L'app raccoglie i dati essenziali della rosa e del giocatore in asta, calcola
la situazione economica e coordina il parere di uno Staff tecnico. Il risultato
deve essere un consiglio pratico e comprensibile: comprare, rilanciare entro
un limite oppure passare.

## Funzionalità principali

### Gestione dell'asta

- calcolo del budget iniziale e dei crediti già spesi;
- calcolo dei crediti rimanenti;
- calcolo dell'offerta massima teorica;
- riepilogo della composizione della rosa per reparto;
- inserimento del giocatore e del prezzo corrente;
- richiesta di un consiglio all'AI Coach.

### Staff tecnico

Lo Staff d'asta è composto da cinque prospettive coordinate:

- **Head Coach**: sintetizza i pareri e formula la decisione pratica;
- **Direttore Sportivo**: valuta prezzo, budget e costruzione della rosa;
- **Responsabile Budget**: protegge i crediti e definisce il tetto economico;
- **Analista Mantra**: legge ruoli e coperture della rosa;
- **Scout**: valuta il giocatore solo sulla base dei dati disponibili.

Il sistema non effettua cinque chiamate indipendenti: i ruoli contribuiscono
alla stessa consultazione e il Coach coordina la risposta finale.

### Interfaccia visiva

Il prototipo frontend contiene una pagina HTML indipendente con:

- schede interattive dei membri dello Staff;
- finestra di dettaglio per ogni profilo;
- tema scuro e possibilità di passare al tema chiaro;
- layout responsive per desktop e dispositivi mobili;
- sezioni dedicate ad Asta e Matchday.

## Struttura del progetto

```text
Fantamantra-ai/
├── analytics/       # Analisi di forma, disponibilità e profili giocatore
├── api/              # Integrazioni e dati esterni
├── data/             # Dati locali di giocatori e competizioni
├── db/               # Importazione e gestione del database
├── engine/           # Motori tattici, ruoli, formazioni e giornata
├── pages/            # Pagine Streamlit dell'app
├── scripts/          # Script di manutenzione e migrazione dati
├── staff/            # Definizione dei ruoli dello Staff
├── tests/            # Test automatici
├── index.html        # Prototipo visuale frontend
├── Style/style.css   # Stili del prototipo frontend
├── script.js         # Interazioni del prototipo frontend
└── app.py            # Applicazione principale Streamlit
```

## Avvio locale

Installare le dipendenze:

```bash
pip install -r requirements.txt
```

Configurare le variabili locali copiando `.env.example` in `.env` e inserendo
le chiavi dei servizi utilizzati. Il file `.env` è escluso dalla repository e
non deve essere condiviso.

Avviare l'applicazione principale:

```bash
streamlit run app.py
```

Dal menu dell'app è possibile aprire la pagina **Staff Visuale**, che integra
il prototipo HTML/CSS/JavaScript dentro Streamlit. Il prototipo può anche
essere aperto autonomamente aprendo `index.html` in un browser.

Per eseguire i test:

```bash
python -m pytest
```

Il test del contesto AI verifica che budget, prezzo, rosa e limite massimo
vengano trasferiti correttamente allo Staff senza effettuare chiamate esterne.

## Stato del progetto

La parte relativa all'asta e al consulto AI è la base attiva del progetto.
L'interfaccia HTML/CSS/JavaScript è in fase di costruzione e serve a dare una
faccia più chiara allo Staff. Le funzionalità Matchday restano in pausa finché
presenze, disponibilità e dati della rosa non saranno collegati in modo
sufficientemente affidabile.

La pagina visuale è già collegata ai dati di budget, rosa, giocatore in asta e
AI Coach. Le interazioni JavaScript gestiscono navigazione, profili e tema;
Streamlit gestisce lo stato e le chiamate al backend.

## Principi del progetto

- separare i calcoli certi dalle valutazioni strategiche;
- non inventare dati mancanti sul giocatore;
- non superare il limite economico calcolato;
- rendere visibili fonti, limiti e incertezze del consiglio;
- costruire l'interfaccia e le funzionalità in modo progressivo.
