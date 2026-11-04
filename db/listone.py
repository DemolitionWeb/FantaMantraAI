"""Importazione del listone Fantacalcio nell'anagrafica giocatori.

Il listone è un CSV senza intestazione, esportato da FantaAsta / Leghe
Fantacalcio. Ogni giocatore viene collegato a quello già presente nel
database (stesso ID Fantacalcio, oppure stessa squadra e nome
compatibile: "Martinez L." e "Lautaro Martínez" sono la stessa persona).
Se nel database esistono più righe per lo stesso giocatore (per esempio
una creata dalla rosa e una dalle partite BBS) vengono unite in una sola,
spostando presenze, infortuni e collegamenti alle fonti.
"""

import csv
import re
import unicodedata
from datetime import datetime, timezone

from db.database import get_connection
from engine.role_engine import normalizza_ruoli
from squadre import nome_canonico


FONTE = "FANTACALCIO"

# Posizione delle colonne nel CSV (il file non ha intestazione). Le
# colonne segnate come "probabile" sono state dedotte dai valori.
COLONNE_CSV = {
    "fantacalcio_id": 0,
    "nome": 1,
    "ruolo_classic": 3,
    "ruoli_mantra": 4,
    "qi_classic": 5,    # probabile
    "qa_classic": 6,    # probabile
    "qi_mantra": 7,     # probabile
    "qa_mantra": 8,     # probabile
    "squadra": 9,
    "fvm_classic": 10,  # probabile
    "fvm_mantra": 11,   # probabile
    "media_voto": 17,   # probabile
    "fanta_media": 18,  # probabile
    "presenze": 19,     # probabile
    "eta": 20,          # probabile
}

INTERI = {
    "qi_classic", "qa_classic", "qi_mantra", "qa_mantra",
    "fvm_classic", "fvm_mantra", "presenze", "eta",
}
DECIMALI = {"media_voto", "fanta_media"}


# ---------------------------------------------------------------------
# Lettura del file
# ---------------------------------------------------------------------

def _numero(valore, tipo):
    valore = (valore or "").strip().replace(",", ".")
    if not valore:
        return None
    try:
        return tipo(float(valore)) if tipo is int else tipo(valore)
    except ValueError:
        return None


def leggi_listone_csv(percorso):
    """Legge il CSV del listone e restituisce una lista di dizionari."""
    giocatori = []

    with open(percorso, encoding="utf-8-sig", newline="") as file:
        for riga in csv.reader(file):
            if len(riga) <= max(COLONNE_CSV.values()) or not riga[0].strip():
                continue

            dati = {}
            for campo, indice in COLONNE_CSV.items():
                valore = riga[indice].strip()
                if campo in INTERI:
                    valore = _numero(valore, int)
                elif campo in DECIMALI:
                    valore = _numero(valore, float)
                dati[campo] = valore

            dati["squadra"] = nome_canonico(dati["squadra"])
            dati["ruoli_mantra"] = ", ".join(normalizza_ruoli(dati["ruoli_mantra"]))
            giocatori.append(dati)

    return giocatori


# ---------------------------------------------------------------------
# Confronto tra nomi scritti in formati diversi
# ---------------------------------------------------------------------

def _parti_nome(nome):
    """Divide un nome in parole intere e iniziali.

    "Martinez L." -> ({"martinez"}, ["l"]); "Esposito F.P." ->
    ({"esposito"}, ["f", "p"]); "Martinez Jo." -> ({"martinez"}, ["jo"]).
    """
    testo = unicodedata.normalize("NFKD", str(nome or "")).casefold()
    testo = "".join(c for c in testo if not unicodedata.combining(c))
    testo = testo.replace("'", "").replace("’", "")
    # Lettere che NFKD non scompone (es. "ł" polacca).
    testo = testo.translate(str.maketrans({"ł": "l", "ø": "o", "đ": "d", "ß": "ss"}))

    parole, iniziali = set(), []
    for pezzo in re.split(r"[\s\-]+", testo):
        if not pezzo:
            continue
        abbreviato = pezzo.endswith(".")
        frammenti = [f for f in re.split(r"[^a-z0-9]+", pezzo) if f]
        for frammento in frammenti:
            if abbreviato or len(frammento) == 1:
                iniziali.append(frammento)
            else:
                parole.add(frammento)

    return parole, iniziali


def _iniziali_coerenti(iniziali, parole, parole_altre, iniziali_altre):
    """Le iniziali di un nome devono corrispondere al nome proprio
    dell'altro, se l'altro lo riporta (come parola in più o iniziale).
    Se l'altro riporta solo il cognome, non c'è nulla da contraddire."""
    candidati = list(parole_altre - parole) + list(iniziali_altre)
    if not candidati:
        return True
    return all(
        any(c.startswith(iniziale) or iniziale.startswith(c) for c in candidati)
        for iniziale in iniziali
    )


def nomi_compatibili(primo, secondo):
    """True se i due nomi possono indicare lo stesso giocatore.

    Le parole intere di uno devono essere contenute in quelle dell'altro
    e le iniziali non devono contraddirsi: "Martinez L." è compatibile
    con "Lautaro Martínez" ma non con "J. Martínez".
    """
    parole_a, iniziali_a = _parti_nome(primo)
    parole_b, iniziali_b = _parti_nome(secondo)

    if not parole_a or not parole_b:
        return False
    if not (parole_a <= parole_b or parole_b <= parole_a):
        return False

    return (
        _iniziali_coerenti(iniziali_a, parole_a, parole_b, iniziali_b)
        and _iniziali_coerenti(iniziali_b, parole_b, parole_a, iniziali_a)
    )


# ---------------------------------------------------------------------
# Unione di righe duplicate
# ---------------------------------------------------------------------

def unisci_giocatori(conn, tieni, elimina):
    """Sposta tutti i riferimenti da `elimina` a `tieni` e cancella `elimina`."""
    # Tabelle con un vincolo di unicità che include giocatore_id: le righe
    # che andrebbero in conflitto restano su `elimina` e vengono rimosse.
    for tabella in ("presenze", "giocatori_fonti", "rosa", "rose_lega", "listone"):
        conn.execute(
            f"UPDATE OR IGNORE {tabella} SET giocatore_id = ? WHERE giocatore_id = ?",
            (tieni, elimina),
        )
        conn.execute(f"DELETE FROM {tabella} WHERE giocatore_id = ?", (elimina,))

    for tabella in ("player_sources", "infortuni"):
        conn.execute(
            f"UPDATE {tabella} SET giocatore_id = ? WHERE giocatore_id = ?",
            (tieni, elimina),
        )

    conn.execute("DELETE FROM giocatori WHERE id = ?", (elimina,))


# ---------------------------------------------------------------------
# Importazione
# ---------------------------------------------------------------------

def _scegli_da_tenere(righe, collegato, in_rosa, id_atteso):
    if collegato in righe:
        return collegato
    for riga in sorted(righe):
        if riga in in_rosa:
            return riga
    if id_atteso in righe:
        return id_atteso
    return sorted(righe)[0]


def importa_listone(percorso):
    """Importa il listone e restituisce un riepilogo dell'operazione."""
    listone = leggi_listone_csv(percorso)
    if not listone:
        raise ValueError(f"Nessun giocatore letto da {percorso}: file vuoto o formato diverso.")
    adesso = datetime.now(timezone.utc).isoformat()
    riepilogo = {"letti": len(listone), "nuovi": 0, "collegati": 0,
                 "uniti": [], "rimossi_dal_listone": 0}

    conn = get_connection()
    try:
        esistenti = {
            gid: (nome, nome_canonico(squadra))
            for gid, nome, squadra in conn.execute(
                "SELECT id, nome, squadra FROM giocatori"
            )
        }
        collegati = dict(conn.execute(
            "SELECT fonte_id, giocatore_id FROM giocatori_fonti WHERE fonte = ?",
            (FONTE,),
        ).fetchall())
        in_rosa = {r[0] for r in conn.execute("SELECT giocatore_id FROM rosa")}

        # 1. Assegna ogni riga esistente a un solo giocatore del listone.
        assegnati = {}  # indice listone -> set di giocatore_id
        gia_assegnati = set()

        for indice, giocatore in enumerate(listone):
            collegato = collegati.get(giocatore["fantacalcio_id"])
            if collegato in esistenti:
                assegnati.setdefault(indice, set()).add(collegato)
                gia_assegnati.add(collegato)

        per_squadra = {}
        for indice, giocatore in enumerate(listone):
            per_squadra.setdefault(giocatore["squadra"], []).append(indice)

        for gid, (nome, squadra) in esistenti.items():
            if gid in gia_assegnati:
                continue
            compatibili = [
                indice for indice in per_squadra.get(squadra, [])
                if nomi_compatibili(listone[indice]["nome"], nome)
            ]
            if not compatibili:
                # Giocatore trasferito: la riga esistente ha la squadra
                # vecchia. Si accetta solo un nome con le stesse parole e
                # unico in tutto il listone.
                parole = _parti_nome(nome)[0]
                compatibili = [
                    indice for indice, altro in enumerate(listone)
                    if _parti_nome(altro["nome"])[0] == parole
                    and nomi_compatibili(altro["nome"], nome)
                ]
            if len(compatibili) == 1:
                assegnati.setdefault(compatibili[0], set()).add(gid)

        # 2. Crea, aggiorna o unisce.
        id_importati = []
        for indice, giocatore in enumerate(listone):
            id_atteso = f"{giocatore['nome']}-{giocatore['squadra']}"
            righe = assegnati.get(indice, set())

            if righe:
                tieni = _scegli_da_tenere(
                    righe, collegati.get(giocatore["fantacalcio_id"]),
                    in_rosa, id_atteso,
                )
                for altra in sorted(righe - {tieni}):
                    unisci_giocatori(conn, tieni, altra)
                    riepilogo["uniti"].append((esistenti[altra][0], esistenti[tieni][0]))
                conn.execute(
                    "UPDATE giocatori SET nome = ?, squadra = ?, ruoli_mantra = ?,"
                    " ultimo_aggiornamento = ? WHERE id = ?",
                    (giocatore["nome"], giocatore["squadra"],
                     giocatore["ruoli_mantra"], adesso, tieni),
                )
                riepilogo["collegati"] += 1
            else:
                tieni = id_atteso
                if conn.execute(
                    "SELECT 1 FROM giocatori WHERE id = ?", (tieni,)
                ).fetchone():
                    # Omonimo nella stessa squadra: l'ID Fantacalcio
                    # rende l'identificativo univoco.
                    tieni = f"{id_atteso}-{giocatore['fantacalcio_id']}"
                conn.execute(
                    "INSERT INTO giocatori (id, nome, squadra, ruoli_mantra,"
                    " fonte, fonte_id, ultimo_aggiornamento)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (tieni, giocatore["nome"], giocatore["squadra"],
                     giocatore["ruoli_mantra"], FONTE,
                     giocatore["fantacalcio_id"], adesso),
                )
                riepilogo["nuovi"] += 1

            conn.execute(
                "INSERT INTO giocatori_fonti (giocatore_id, fonte, fonte_id,"
                " ultimo_aggiornamento) VALUES (?, ?, ?, ?)"
                " ON CONFLICT(giocatore_id, fonte) DO UPDATE SET"
                " fonte_id = excluded.fonte_id,"
                " ultimo_aggiornamento = excluded.ultimo_aggiornamento",
                (tieni, FONTE, giocatore["fantacalcio_id"], adesso),
            )
            conn.execute(
                "INSERT OR REPLACE INTO player_sources (giocatore_id, fonte, fonte_id)"
                " VALUES (?, ?, ?)",
                (tieni, FONTE, giocatore["fantacalcio_id"]),
            )

            campi = [c for c in COLONNE_CSV if c != "fantacalcio_id"]
            conn.execute(
                f"INSERT OR REPLACE INTO listone (giocatore_id, fantacalcio_id,"
                f" {', '.join(campi)}, ultimo_aggiornamento)"
                f" VALUES ({', '.join('?' for _ in range(len(campi) + 3))})",
                (tieni, giocatore["fantacalcio_id"],
                 *(giocatore[c] for c in campi), adesso),
            )
            id_importati.append(tieni)

        # 3. Chi non è più nel listone (es. ceduto all'estero) esce dal
        # listone ma resta in anagrafica con il suo storico.
        segnaposti = ", ".join("?" for _ in id_importati)
        riepilogo["rimossi_dal_listone"] = conn.execute(
            f"DELETE FROM listone WHERE giocatore_id NOT IN ({segnaposti})",
            id_importati,
        ).rowcount

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return riepilogo
