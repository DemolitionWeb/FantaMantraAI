import shutil
import tempfile
from pathlib import Path

import pytest

import db.database as database
import player_identity
from db.calendario import salva_calendario, trasforma_partite
from db.classifica import salva_classifica
from db.lega import dati_listone, proprietario
from engine.match_difficult import calcola_match_difficulty, stima_difficolta


@pytest.fixture
def db_vuoto(monkeypatch):
    cartella = Path(tempfile.mkdtemp(prefix="fantamantra-test-"))
    monkeypatch.setattr(database, "DB_PATH", cartella / "test.db")
    database.crea_database()
    yield database
    shutil.rmtree(cartella, ignore_errors=True)


def _squadra(posizione, gol_fatti, gol_subiti, punti):
    return {"posizione": posizione, "giocate": 10, "punti": punti,
            "gol_fatti": gol_fatti, "gol_subiti": gol_subiti,
            "attacco": gol_fatti / 10, "difesa": gol_subiti / 10}


CLASSIFICA = {
    "Lazio": _squadra(1, 24, 8, 28),
    "Napoli": _squadra(2, 17, 13, 14),
    "Venezia": _squadra(3, 6, 20, 3),
}


def test_capolista_in_trasferta_e_piu_difficile_dell_ultima_in_casa():
    contro_lazio = stima_difficolta("Lazio", "trasferta", CLASSIFICA)
    contro_venezia = stima_difficolta("Venezia", "casa", CLASSIFICA)

    # Lazio: 1ª, miglior attacco e miglior difesa -> 100, +7,5 in trasferta.
    assert contro_lazio["difficulty_score"] == 100.0
    # Venezia: ultima, peggior attacco e difesa -> 0, -7,5 in casa.
    assert contro_venezia["difficulty_score"] == 0.0
    assert contro_lazio["confidence"] == 100
    assert "Lazio è 1°" in contro_lazio["reason"]


def test_casa_e_trasferta_cambiano_la_difficolta():
    casa = stima_difficolta("Napoli", "casa", CLASSIFICA)["difficulty_score"]
    trasferta = stima_difficolta("Napoli", "trasferta", CLASSIFICA)["difficulty_score"]

    assert trasferta - casa == pytest.approx(15.0)


def test_senza_classifica_nessuna_stima():
    assert stima_difficolta("Lazio", "casa", {}) is None


RISPOSTA_PARTITE = {"matches": [
    {"id": 1, "matchday": 11, "utcDate": "2099-11-08T11:30:00Z",
     "status": "TIMED",
     "homeTeam": {"shortName": "Napoli"}, "awayTeam": {"shortName": "Lazio"},
     "score": {"fullTime": {"home": None, "away": None}}},
    {"id": 2, "matchday": 1, "utcDate": "2026-08-22T18:45:00Z",
     "status": "FINISHED",
     "homeTeam": {"shortName": "Inter"}, "awayTeam": {"shortName": "Venezia FC"},
     "score": {"fullTime": {"home": 3, "away": 0}}},
]}


def test_trasforma_partite():
    partite = trasforma_partite(RISPOSTA_PARTITE)

    assert partite[0]["id"] == "FD-1"
    assert partite[0]["stato"] == "scheduled"
    assert partite[1]["squadra_trasferta"] == "Venezia"
    assert (partite[1]["gol_casa"], partite[1]["gol_trasferta"]) == (3, 0)


def test_calendario_aggiorna_partite_bbs_senza_cambiare_id(db_vuoto):
    # Partita salvata da BBS, con una presenza collegata.
    db_vuoto.salva_partite([{
        "id": "bbs-1", "squadra_casa": "Inter Milan",
        "squadra_trasferta": "Venezia FC",
        "kickoff_utc": "2026-08-22T18:45:00.000Z", "stato": "scheduled",
    }])

    nuove, aggiornate = salva_calendario(trasforma_partite(RISPOSTA_PARTITE))

    assert (nuove, aggiornate) == (1, 1)
    conn = db_vuoto.get_connection()
    stato = conn.execute(
        "SELECT stato, gol_casa FROM partite WHERE id = 'bbs-1'"
    ).fetchone()
    totale = conn.execute("SELECT COUNT(*) FROM partite").fetchone()[0]
    conn.close()
    assert stato == ("finished", 3)
    assert totale == 2

    # Ripetere l'importazione non duplica nulla.
    assert salva_calendario(trasforma_partite(RISPOSTA_PARTITE)) == (0, 2)


def test_difficolta_della_prossima_partita_dal_database(db_vuoto):
    salva_calendario(trasforma_partite(RISPOSTA_PARTITE))
    salva_classifica([
        {"tipo": "TOTAL", "squadra_id": i, "squadra": nome, "posizione": pos,
         "punti": pt, "giocate": 10, "gol_fatti": gf, "gol_subiti": gs}
        for i, (nome, pos, pt, gf, gs) in enumerate([
            ("Lazio", 1, 28, 24, 8), ("Napoli", 8, 14, 17, 13),
            ("Venezia", 20, 3, 6, 20),
        ])
    ])

    partita = calcola_match_difficulty("SSC Napoli")

    assert partita["avversario"] == "Lazio"
    assert partita["casa_trasferta"] == "casa"
    # La partita del 2026 è passata: conta solo quella futura.
    assert partita["match_id"] == "FD-1"
    assert partita["difficulty_score"] == 92.5


def test_profilo_giocatore_con_nome_in_altro_formato(db_vuoto):
    conn = db_vuoto.get_connection()
    conn.executescript("""
        INSERT INTO giocatori (id, nome, squadra, ruoli_mantra) VALUES
            ('lm', 'Martinez L.', 'Inter', 'PC'),
            ('jm', 'Martinez Jo.', 'Inter', 'POR');
        INSERT INTO listone (giocatore_id, fantacalcio_id, nome, squadra,
                             qa_mantra, fvm_mantra)
        VALUES ('lm', '2764', 'Martinez L.', 'Inter', 35, 350),
               ('jm', '2001', 'Martinez Jo.', 'Inter', 6, 20);
        INSERT INTO fantasquadre (id, nome, mia) VALUES (1, 'REAL DOBAGLIO', 0);
        INSERT INTO rose_lega (giocatore_id, fantasquadra_id, costo)
        VALUES ('lm', 1, 85);
    """)
    conn.commit()
    conn.close()

    profilo = player_identity.trova_giocatore_per_nome("Lautaro Martinez")

    assert profilo["id"] == "lm"
    # Il solo cognome è ambiguo: nessun profilo.
    assert player_identity.trova_giocatore_per_nome("Martinez") is None
    assert proprietario("lm") == {"squadra": "REAL DOBAGLIO", "mia": False, "costo": 85}
    assert proprietario("jm") is None
    assert dati_listone("lm")["fvm_mantra"] == 350
