import shutil
import tempfile
from pathlib import Path

import pytest

import db.database as database
from analytics.form_engine import calcola_form
from auction_engine import offerta_massima
from db.infortuni import chiudi_infortuni_assenti, salva_infortunio
from engine import schierabilita_engine
from engine.bench_engine import crea_panchina


@pytest.fixture
def db_vuoto(monkeypatch):
    cartella = Path(tempfile.mkdtemp(prefix="fantamantra-test-"))
    monkeypatch.setattr(database, "DB_PATH", cartella / "test.db")
    database.crea_database()
    yield database
    shutil.rmtree(cartella, ignore_errors=True)


def _giocatore(gid, ruoli, score):
    return {
        "giocatore_id": gid,
        "ruoli_mantra": ruoli,
        "score": score,
        "disponibile": True,
    }


def test_offerta_massima_conserva_un_credito_per_ogni_posto_libero():
    # 100 crediti, 10 posti: 9 crediti restano per gli altri 9 posti.
    assert offerta_massima(500, 400, posti_da_riempire=10) == 91
    assert offerta_massima(500, 400, posti_da_riempire=1) == 100
    assert offerta_massima(500, 400, posti_da_riempire=0) == 0
    assert offerta_massima(500, 495, posti_da_riempire=10) == 0


def test_panchina_non_ripete_lo_stesso_giocatore():
    giocatori = [
        _giocatore("esterno", "E, M", 90),
        _giocatore("dc", "DC", 80),
        _giocatore("cc", "C", 70),
        _giocatore("att", "A", 60),
    ]

    panchina = crea_panchina(giocatori, titolari=[])

    ids = [g["giocatore_id"] for gruppo in panchina.values() for g in gruppo]
    assert len(ids) == len(set(ids))
    assert [g["giocatore_id"] for g in panchina["DIF"]] == ["esterno", "dc"]
    assert [g["giocatore_id"] for g in panchina["CEN"]] == ["cc"]


def test_crea_database_permette_di_salvare_giocatori(db_vuoto):
    db_vuoto.salva_giocatori([
        {"id": "g1", "nome": "Mario Rossi", "squadra": "Roma",
         "fonte": "BBS", "fonte_id": "42"},
    ])
    assert db_vuoto.conta_giocatori() == 1


def test_salva_identificativo_fonte_aggiorna_entrambi_i_registri(db_vuoto):
    db_vuoto.salva_identificativo_fonte("g1", "BBS", "42", "2026-10-01")

    assert db_vuoto.trova_id_fonte("g1", "BBS") == "42"
    assert db_vuoto.trova_giocatore_per_source("BBS", "42") == "g1"

    conn = db_vuoto.get_connection()
    data = conn.execute(
        "SELECT ultimo_aggiornamento FROM giocatori_fonti WHERE giocatore_id = 'g1'"
    ).fetchone()[0]
    conn.close()
    assert data == "2026-10-01"


def _presenza(partita_id, voto):
    return {
        "giocatore_id": "g1", "partita_id": partita_id, "titolare": 1,
        "minuti": 90, "posizione": None, "numero_maglia": None,
        "voto": voto, "gol": 0, "assist": 0,
        "ammonizioni": 0, "espulsioni": 0,
    }


def test_forma_senza_voti_e_dato_mancante(db_vuoto):
    db_vuoto.salva_presenze([_presenza("p1", 0)])

    form = calcola_form("g1")

    assert form["form_score"] is None
    assert form["partite_recenti"] == 1


def test_forma_usa_le_partite_piu_recenti_per_data(db_vuoto):
    partite = [
        {"id": f"p{i}", "kickoff_utc": f"2026-09-{i:02d}T18:00:00Z",
         "squadra_casa": f"Casa{i}", "squadra_trasferta": f"Ospite{i}"}
        for i in range(1, 7)
    ]
    db_vuoto.salva_partite(partite)
    # La partita più vecchia viene importata per ultima: con l'ordinamento
    # per id finirebbe tra le "recenti".
    db_vuoto.salva_presenze([_presenza(f"p{i}", 7.0) for i in range(2, 7)])
    db_vuoto.salva_presenze([_presenza("p1", 4.0)])

    assert calcola_form("g1")["media_voto_recenti"] == 7.0


def test_infortuni_non_piu_in_lista_vengono_chiusi(db_vuoto):
    salva_infortunio("g1", "BBS", "1")
    salva_infortunio("g2", "BBS", "2")

    assert chiudi_infortuni_assenti("BBS", ["g2"]) == 1

    conn = db_vuoto.get_connection()
    stati = dict(conn.execute("SELECT giocatore_id, stato FROM infortuni"))
    conn.close()
    assert stati == {"g1": "risolto", "g2": "attivo"}


def test_confidence_schierabilita_include_la_forma(monkeypatch):
    monkeypatch.setattr(schierabilita_engine, "analizza_giocatore",
                        lambda gid: {"nome": "X", "squadra": None})
    monkeypatch.setattr(schierabilita_engine, "calcola_form",
                        lambda gid: {"form_score": 60, "confidenza": 90})
    monkeypatch.setattr(schierabilita_engine, "calcola_starter_probability",
                        lambda gid: {"starter_probability": 80,
                                     "data_confidence": 90, "media_minuti": 90})
    monkeypatch.setattr(schierabilita_engine, "analizza_disponibilita",
                        lambda gid: {"disponibile": True, "confidence": 90})

    risultato = schierabilita_engine.calcola_schierabilita("g1")

    assert risultato["confidence"] == 90
