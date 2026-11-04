# Fantamantra AI

Assistente per il **Fantacalcio Mantra**, scritto in Python con Streamlit e SQLite.
Lavora durante l'asta (estiva e di riparazione) e durante la stagione:

- conosce **tutto il listone** e **le rose di tutte le squadre della lega**;
- calcola crediti residui, posti liberi e **offerta massima** di ogni squadra;
- durante l'asta dal vivo dice chi possiede un giocatore, **chi può ancora rilanciare** e fino a quanto;
- registra aggiudicazioni e svincoli con le regole della lega (rimborsi, bonus di riparazione);
- stima la **difficoltà della prossima partita** dalla classifica di Serie A;
- chiede un consiglio a un **AI Coach** che coordina uno "Staff tecnico" virtuale, usando solo dati verificati.

L'idea d'uso è a **due dispositivi**: su uno si chiama e si rilancia (app di Leghe Fantacalcio), sull'altro si tiene aperta la pagina *Asta live* di Fantamantra.

---

## Indice

1. [Requisiti](#requisiti)
2. [Installazione](#installazione)
3. [Configurazione delle chiavi](#configurazione-delle-chiavi)
4. [Dati della lega](#dati-della-lega)
5. [Popolare il database](#popolare-il-database)
6. [Avvio](#avvio)
7. [Le pagine dell'app](#le-pagine-dellapp)
8. [Architettura](#architettura)
9. [Modello dati](#modello-dati)
10. [Logiche principali](#logiche-principali)
11. [Test](#test)
12. [Limiti noti e roadmap](#limiti-noti-e-roadmap)

---

## Requisiti

| Componente | Versione / note |
|---|---|
| Python | 3.12 (sviluppato e testato con 3.12.9) |
| Sistema operativo | Sviluppato su Windows; nessuna dipendenza specifica di Windows nel codice |
| Database | SQLite, incluso in Python: nessun server da installare |
| Account esterni | football-data.org (gratuito), OpenAI (per l'AI Coach), BigBalls (facoltativo) |

Dipendenze Python ([requirements.txt](requirements.txt)): `streamlit`, `pandas`, `openpyxl`, `openai`, `requests`, `python-dotenv`, `pytest`.

## Installazione

```bash
git clone git@github.com:DemolitionWeb/FantaMantraAI.git
cd FantaMantraAI

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Il database (`db/fantamantra.db`) **non è nel repository**: viene creato in automatico al primo avvio dell'app o di uno script di importazione (`crea_database()` in [db/database.py](db/database.py)). Lo schema si aggiorna da solo: le tabelle nuove vengono create e le colonne mancanti aggiunte, senza toccare i dati.

## Configurazione delle chiavi

Copia [.env.example](.env.example) in `.env` e compila le chiavi. Il file `.env` è escluso da git.

| Variabile | Serve per | Obbligatoria? | Dove ottenerla |
|---|---|---|---|
| `FOOTBALL_DATA_API_TOKEN` | Classifica e calendario di Serie A, difficoltà delle partite | Consigliata | Registrazione gratuita su https://www.football-data.org/client/register (piano free: Serie A inclusa, 10 richieste/minuto) |
| `OPENAI_API_KEY` | Consiglio dell'AI Coach | Solo per il consiglio AI | https://platform.openai.com |
| `BBS_API_KEY` | Infortuni e presenze da BigBalls (`api.bigballsdata.com`) | Facoltativa | Account presso il fornitore BigBalls |
| `SPORTMONKS_API_TOKEN` | Non usata dal codice attuale (prove precedenti) | No | — |

Senza chiavi l'app funziona comunque: asta, lega, svincoli e calcoli dei crediti usano solo il database locale. Le chiavi abilitano le funzioni che dipendono da servizi esterni.

Il modello OpenAI è impostato in [ai_coach.py](ai_coach.py) (`chiedi_consiglio`).

## Dati della lega

Listone e rose arrivano da **esportazioni manuali** di Fantacalcio / Leghe Fantacalcio.
I termini d'uso di Fantacalcio.it vietano lo scraping, quindi il progetto non scarica nulla in automatico da quel sito: i file vanno esportati a mano e copiati in `data/`.

| File | Nome atteso | Origine | Formato |
|---|---|---|---|
| Listone | `data/listone_<data>.csv` | Esportazione "calciatori" di FantaAsta / Leghe Fantacalcio | CSV **senza intestazione**, 22 colonne (vedi sotto) |
| Rose della lega | `data/rose_lega_<data>.xlsx` | Leghe Fantacalcio → esportazione rose | Excel: per ogni squadra una colonna *nome squadra* e una *costo*, separate da una colonna vuota, con una riga `totale` in fondo |
| Rosa personale (facoltativa) | percorso in `FILE_ROSA` di [db/import_rosa.py](db/import_rosa.py) | Leghe Fantacalcio → la mia rosa | CSV con `;`, intestazione `Ruolo;Nome;Squadra;Costo d'acquisto;...` |

Colonne del listone usate dall'importatore ([db/listone.py](db/listone.py), `COLONNE_CSV`):

| Indice | Campo | Note |
|---|---|---|
| 0 | ID Fantacalcio | Chiave stabile del giocatore |
| 1 | Nome | Formato "Cognome I." (es. `Martinez L.`) |
| 3 | Ruolo Classic | P / D / C / A |
| 4 | Ruoli Mantra | Separati da `;` (es. `W;A`) |
| 5–8 | Quotazioni iniziale e attuale, Classic e Mantra | Dedotte dai valori |
| 9 | Squadra di Serie A | |
| 10–11 | FVM Classic e Mantra | Dedotte dai valori |
| 17–20 | Media voto, fantamedia, presenze, età | Dedotte dai valori |

Se il formato dell'esportazione cambia, basta aggiornare `COLONNE_CSV`.

> **Privacy.** Le rose contengono dati privati della lega: `data/rose_lega_*.xlsx` è in `.gitignore`. Il database `*.db` è escluso da git.

## Popolare il database

Ordine consigliato, dalla cartella del progetto con il virtualenv attivo:

```bash
# 1. Listone + rose della lega (usa i file più recenti in data/)
python -m scripts.importa_listone_rose
#    se la tua squadra non viene riconosciuta in automatico:
python -m scripts.importa_listone_rose --mia "Nome della tua squadra"

# 2. Classifica e calendario di Serie A (football-data.org)
python -m scripts.importa_classifica

# 3. Facoltativo: infortuni da BigBalls
python -m scripts.importa_infortuni
```

Tutti gli script si possono **rilanciare** senza creare duplicati:

- `importa_listone_rose` collega i giocatori a quelli esistenti e **unisce i doppioni**, spostando presenze, infortuni e ID esterni sulla riga che resta;
- `importa_classifica` aggiorna le partite già salvate senza cambiarne l'ID;
- `importa_infortuni` segna come "risolti" gli infortuni non più presenti nella lista della fonte.

Altri script utili in [scripts/](scripts/):

| Script | Uso |
|---|---|
| `allinea_nomi_squadre` | Migra ai nomi canonici le squadre di database creati prima dell'allineamento |
| `controlla_database`, `controlla_partite`, `controlla_infortuni` | Controlli rapidi del contenuto del DB |
| `pulisci_presenze`, `ricollega_presenze_rosa`, `migra_players_sources` | Manutenzione di dati storici |

## Avvio

```bash
python -m streamlit run app.py
```

Si apre il browser su `http://localhost:8501`. Le pagine sono nella barra laterale.

**Uso da un secondo dispositivo sulla stessa rete Wi-Fi** (es. telefono o tablet durante l'asta):

```bash
python -m streamlit run app.py --server.address 0.0.0.0
```

e dal dispositivo apri `http://<IP-del-PC>:8501`. Su Windows potrebbe servire consentire Python nel firewall. I dati restano sul PC.

## Le pagine dell'app

| Pagina | File | A cosa serve |
|---|---|---|
| **app** | [app.py](app.py) | Asta "classica": budget, giocatore in asta con valori del listone e proprietario, AI Coach, rosa inserita a mano |
| **Staff Visuale** | [pages/0_Staff_Visuale.py](pages/0_Staff_Visuale.py) | Prototipo HTML/CSS/JS ([index.html](index.html), [Style/style.css](Style/style.css), [script.js](script.js)) riempito con dati veri: profilo del giocatore, crediti della lega, svincolati, difficoltà delle partite |
| **Staff Tecnico** | [pages/1_Staff_Tecnico.py](pages/1_Staff_Tecnico.py) | Descrizione dei ruoli dello Staff e dei loro limiti |
| **Lega** | [pages/2_Lega.py](pages/2_Lega.py) | Crediti di tutte le squadre, rose, svincolati filtrabili per ruolo Mantra, club e nome |
| **Asta live** | [pages/3_Asta_live.py](pages/3_Asta_live.py) | Schermata per il secondo dispositivo: ricerca rapida, rivali che possono rilanciare, aggiudica, svincola, annulla, regole della lega |

`index.html` aperto da solo nel browser mostra la versione statica: le sezioni con i dati si riempiono solo quando la pagina viene servita da *Staff Visuale*. I punti di inserimento sono i commenti `<!-- STREAMLIT_* -->` nell'HTML.

## Architettura

```text
              ┌──────────────────────────── fonti ────────────────────────────┐
              │ Listone CSV · Rose XLSX   football-data.org   BigBalls   OpenAI │
              └──────┬───────────────────────────┬──────────────┬────────┬────┘
                     │                           │              │        │
          db/listone.py, db/lega.py     api/football_data.py  api/bigballs.py  ai_coach.py
                     │                  db/classifica.py      db/presenze.py       │
                     │                  db/calendario.py      db/infortuni.py      │
                     ▼                           ▼              ▼                 │
              ┌────────────────────── SQLite: db/fantamantra.db ──────────────┐  │
              └──────┬───────────────────────────┬────────────────────────────┘  │
                     │                           │                               │
             db/mercato.py               analytics/ + engine/                    │
     (regole, crediti, aggiudica,   (forma, disponibilità, titolarità,           │
          svincola, annulla)         difficoltà, schierabilità, moduli)          │
                     │                           │                               │
                     └──────────────► pagine Streamlit ◄───────────────────────────┘
```

| Cartella / file | Responsabilità |
|---|---|
| [api/](api/) | Client HTTP verso servizi esterni (football-data.org, BigBalls) |
| [db/](db/) | Schema, importazioni, accesso ai dati, mercato |
| [analytics/](analytics/) | Statistiche del giocatore: forma, disponibilità, profilo |
| [engine/](engine/) | Motori di calcolo: difficoltà partita, schierabilità, ruoli, moduli, panchina |
| [staff/](staff/) | Definizione dei ruoli dello Staff e del contesto per l'AI |
| [squadre.py](squadre.py) | Nomi canonici delle squadre di Serie A |
| [auction_engine.py](auction_engine.py) | Calcoli di budget e offerta massima per l'asta classica |
| [stato_app.py](stato_app.py) | Stato condiviso tra le pagine Streamlit |
| [pages/](pages/) | Pagine dell'app |
| [tests/](tests/) | Test automatici (vedi [Test](#test)) |
| [docs/staff_design.md](docs/staff_design.md) | Progetto dello Staff tecnico |

## Modello dati

Tabelle principali, create da `crea_database()`:

| Tabella | Contenuto | Chiave |
|---|---|---|
| `giocatori` | Anagrafica unica dei giocatori | `id` (testo, es. `Martinez L.-Inter`) |
| `listone` | Ruoli Mantra, quotazioni, FVM, fantamedia dal listone | `giocatore_id`, `fantacalcio_id` univoco |
| `giocatori_fonti`, `player_sources` | ID dei giocatori nelle fonti esterne (FANTACALCIO, BBS) | (giocatore, fonte) / (fonte, id esterno) |
| `fantasquadre` | Squadre della lega, con `mia = 1` per la propria | `id` |
| `rose_lega` | Chi possiede chi e a che prezzo | `giocatore_id` (un giocatore, una squadra) |
| `impostazioni_lega` | Regole: budget, bonus, massimo giocatori, rimborsi | `chiave` |
| `movimenti_lega` | Storico di acquisti e svincoli dell'asta dal vivo, con annullamento | `id` |
| `partite` | Calendario e risultati di Serie A | `id` (`FD-…` da football-data, UUID da BigBalls) |
| `classifica` | Classifica di Serie A per tipo (TOTAL, HOME, AWAY) | (`tipo`, `squadra_id`) |
| `presenze` | Minuti, voto, gol, assist per giocatore e partita | (`giocatore_id`, `partita_id`) |
| `infortuni` | Infortuni con fonte, stato (`attivo` / `risolto`) e date | `id` |
| `rosa` | Dettaglio della propria rosa dal CSV personale | `giocatore_id` |
| `rosa_asta` | Rosa inserita a mano nella pagina *app* (in `database.db`) | `id` |

> `rosa_asta` vive in un file separato (`database.db`, nella cartella da cui si avvia l'app): è un residuo della prima versione, da unificare.

## Logiche principali

### Nomi delle squadre ([squadre.py](squadre.py))
Ogni fonte scrive le squadre a modo suo ("AC Milan", "Inter Milan", "Como 1907", "Venezia FC"). `nome_canonico()` le riconduce alla forma del listone ("Milan", "Inter", "Como", "Venezia") ignorando maiuscole, accenti, sigle societarie e anni. Si applica **prima di salvare e prima di confrontare**.

### Collegamento dei giocatori ([db/listone.py](db/listone.py))
Lo stesso giocatore può arrivare come `Martinez L.` (listone), `Lautaro Martínez` o `L. Martinez` (BigBalls). `nomi_compatibili()` confronta le parole del nome e verifica che le iniziali non si contraddicano: `Martinez L.` è compatibile con `Lautaro Martínez` ma non con `J. Martínez`. L'ordine di ricerca è: ID Fantacalcio già noto → stessa squadra e nome compatibile → nome identico e univoco in tutto il listone (per i trasferiti). Un caso ambiguo **non viene mai collegato** a caso.

### Mercato e crediti ([db/mercato.py](db/mercato.py))
```text
residui         = budget iniziale + bonus riparazione
                  − costo dei giocatori in rosa
                  − Σ (costo − rimborso) degli svincoli
offerta massima = residui − (posti liberi − 1)      # 1 credito per ogni altro posto
rimborso        = costo × quota (default 50%, per difetto)
                  oppure costo pieno se il giocatore ha lasciato la Serie A
```
Le regole sono modificabili dalla pagina *Asta live* e salvate in `impostazioni_lega`, senza toccare il codice.

### Difficoltà della partita ([engine/match_difficult.py](engine/match_difficult.py))
Punteggio da 0 (facile) a 100 (difficile) basato sull'avversario: 50% posizione in classifica, 25% gol fatti a partita, 25% gol subiti a partita (scalati sul campionato), ±7,5 per trasferta/casa. Ogni valore è accompagnato da una spiegazione leggibile.

### AI Coach ([ai_coach.py](ai_coach.py), [staff/roles.py](staff/roles.py))
Una sola chiamata al modello, con un contesto che contiene i dati calcolati (budget, tetto, profilo del giocatore, rivali) e i ruoli dello Staff con i loro limiti. Il prompt chiede di separare fatti e valutazioni e di non superare l'offerta massima calcolata.

## Test

```bash
python -m pytest
```

- I test usano database SQLite temporanei: non toccano `db/fantamantra.db` e non fanno chiamate di rete (le API sono simulate).
- Alcuni file `tests/test_*.py` sono **script diagnostici manuali** che interrogano servizi esterni: sono esclusi dalla raccolta in [tests/conftest.py](tests/conftest.py) e si lanciano a mano, es. `python -m tests.test_convertitore`.
- Su Windows, se pytest non riesce a scrivere nella cartella temporanea predefinita (`PermissionError` su `pytest-of-<utente>`), indica un'altra cartella:
  ```bash
  python -m pytest --basetemp=.pytest_tmp
  ```

## Limiti noti e roadmap

- **Presenze storiche**: l'importazione da BigBalls si fa partita per partita con uno script manuale ([tests/test_convertitore.py](tests/test_convertitore.py)). Per questo il Matchday (titolarità e forma della rosa) è ancora poco popolato.
- **Svincoli fatti solo su Leghe Fantacalcio**: l'app non li vede. Vanno registrati anche in *Asta live*, altrimenti il rimborso non viene conteggiato.
- **Colonne del listone**: quotazioni, FVM e statistiche sono state dedotte dai valori (il CSV non ha intestazioni).
- **Due database**: `rosa_asta` della pagina *app* è ancora in `database.db`, separato da `db/fantamantra.db`.
- **Interfaccia**: restyling del prototipo HTML in programma prima del mercato invernale.
- **Prossimi passi**: importazione automatica delle presenze, voti Fantacalcio ufficiali (import manuale), probabili formazioni, squalifiche e diffidati.

## Principi del progetto

- I **calcoli certi** (crediti, tetti, regole) sono deterministici e vincolanti; l'AI li commenta, non li sostituisce.
- **Nessun dato inventato**: se un'informazione manca, l'app lo dice.
- **Fonti esplicite**: ogni dato importato conserva la fonte e la data di aggiornamento.
- **Importazioni ripetibili**: ogni script si può rilanciare senza duplicare o perdere dati.
