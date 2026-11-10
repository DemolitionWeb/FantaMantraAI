import shutil
from datetime import datetime, timedelta, timezone
import tempfile
from pathlib import Path

import pytest

import db.database as database
from analytics.availability_engine import prossima_partita
from scripts.allinea_nomi_squadre import allinea
from squadre import nome_canonico, stessa_squadra


@pytest.mark.parametrize("nome, atteso", [
    # BigBalls
    ("AC Milan", "Milan"),
    ("AS Roma", "Roma"),
    ("Inter Milan", "Inter"),
    # football-data.org
    ("Como 1907", "Como"),
    ("Venezia FC", "Venezia"),
    ("FC Internazionale Milano", "Inter"),
    ("SSC Napoli", "Napoli"),
    ("Bologna FC 1909", "Bologna"),
    ("Parma Calcio 1913", "Parma"),
    ("Hellas Verona FC", "Verona"),
    # Già canonici o con spazi e maiuscole diverse
    ("Inter", "Inter"),
    ("  juventus ", "Juventus"),
])
def test_nome_canonico_riconduce_al_listone(nome, atteso):
    assert nome_canonico(nome) == atteso


def test_squadre_estere_restano_invariate():
    assert nome_canonico("Eintracht Frankfurt") == "Eintracht Frankfurt"
    assert nome_canonico("Croatia") == "Croatia"
    assert nome_canonico(None) is None


def test_stessa_squadra():
    assert stessa_squadra("AC Milan", "Milan")
    assert not stessa_squadra("AC Milan", "Inter")
    assert not stessa_squadra(None, "Milan")


@pytest.fixture
def db_vuoto(monkeypatch):
    cartella = Path(tempfile.mkdtemp(prefix="fantamantra-test-"))
    monkeypatch.setattr(database, "DB_PATH", cartella / "test.db")
    database.crea_database()
    yield database
    shutil.rmtree(cartella, ignore_errors=True)


def test_partite_salvate_con_nome_canonico_e_trovabili(db_vuoto):
    db_vuoto.salva_partite([{
        "id": "m1", "squadra_casa": "AC Milan",
        "squadra_trasferta": "Inter Milan",
        "kickoff_utc": (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ"), "stato": "scheduled",
    }])

    partita = prossima_partita("Milan")

    assert partita["casa"] == "Milan"
    assert partita["trasferta"] == "Inter"
    assert prossima_partita("Inter Milan")["partita_id"] == "m1"


def test_migrazione_allinea_dati_esistenti(db_vuoto):
    # Simula dati salvati prima dell'allineamento.
    conn = db_vuoto.get_connection()
    conn.execute(
        "INSERT INTO partite (id, squadra_casa, squadra_trasferta, kickoff_utc)"
        " VALUES ('m1', 'AS Roma', 'Venezia FC', '2026-11-08')"
    )
    conn.execute(
        "INSERT INTO giocatori (id, nome, squadra) VALUES ('g1', 'X', 'Como 1907')"
    )
    conn.commit()
    conn.close()

    risultato = allinea()

    conn = db_vuoto.get_connection()
    partita = conn.execute(
        "SELECT squadra_casa, squadra_trasferta FROM partite"
    ).fetchone()
    giocatore = conn.execute("SELECT id, squadra FROM giocatori").fetchone()
    conn.close()

    assert partita == ("Roma", "Venezia")
    assert giocatore == ("g1", "Como")
    assert sum(len(v) for v in risultato.values()) == 3
    assert sum(len(v) for v in allinea().values()) == 0
