import shutil
import tempfile
from pathlib import Path

import pytest

import db.database as database
from db.mercato import (
    ErroreMercato,
    aggiudica,
    annulla_ultimo,
    calcola_rimborso,
    leggi_regole,
    rosa_squadra,
    salva_regole,
    situazione_squadre,
    storico_movimenti,
    svincola,
)


@pytest.fixture
def lega(monkeypatch):
    """Due squadre: la mia con 2 giocatori, un rivale con 1.
    'estero' è in rosa ma non più nel listone (ha lasciato la Serie A)."""
    cartella = Path(tempfile.mkdtemp(prefix="fantamantra-test-"))
    monkeypatch.setattr(database, "DB_PATH", cartella / "test.db")
    database.crea_database()

    conn = database.get_connection()
    conn.executescript("""
        INSERT INTO giocatori (id, nome, squadra) VALUES
            ('a', 'Alfa', 'Inter'), ('b', 'Beta', 'Roma'),
            ('c', 'Gamma', 'Milan'), ('libero', 'Delta', 'Lazio'),
            ('estero', 'Omega', 'Napoli');
        INSERT INTO listone (giocatore_id, fantacalcio_id, nome, squadra) VALUES
            ('a', '1', 'Alfa', 'Inter'), ('b', '2', 'Beta', 'Roma'),
            ('c', '3', 'Gamma', 'Milan'), ('libero', '4', 'Delta', 'Lazio');
        INSERT INTO fantasquadre (id, nome, mia) VALUES (1, 'Mia', 1), (2, 'Rivale', 0);
        INSERT INTO rose_lega (giocatore_id, fantasquadra_id, costo) VALUES
            ('a', 1, 100), ('estero', 1, 30), ('c', 2, 495);
    """)
    conn.commit()
    conn.close()

    salva_regole(budget_iniziale=500, bonus_riparazione=50, max_giocatori=4)
    yield
    shutil.rmtree(cartella, ignore_errors=True)


def _squadra(nome):
    return next(s for s in situazione_squadre() if s["squadra"] == nome)


@pytest.mark.parametrize("costo, uscito, arrotondamento, atteso", [
    (2, False, "difetto", 1),
    (5, False, "difetto", 2),
    (5, False, "eccesso", 3),
    (1, False, "difetto", 0),
    (30, True, "difetto", 30),
])
def test_calcola_rimborso(costo, uscito, arrotondamento, atteso):
    regole = {"quota_rimborso": 0.5, "arrotondamento": arrotondamento}
    assert calcola_rimborso(costo, uscito, regole) == atteso


def test_regole_predefinite_e_salvate(lega):
    regole = leggi_regole()
    assert regole["bonus_riparazione"] == 50
    assert regole["max_giocatori"] == 4
    assert regole["quota_rimborso"] == 0.5


def test_situazione_con_bonus_posti_e_offerta_massima(lega):
    mia = _squadra("Mia")
    # 500 + 50 - 130 spesi; 2 posti liberi -> si conserva 1 credito.
    assert (mia["residui"], mia["posti_liberi"], mia["offerta_massima"]) == (420, 2, 419)

    rivale = _squadra("Rivale")
    assert (rivale["residui"], rivale["offerta_massima"]) == (55, 53)


def test_aggiudica_aggiorna_rosa_e_crediti(lega):
    messaggio = aggiudica("libero", "Rivale", 20)

    assert "Delta a Rivale per 20" in messaggio
    rivale = _squadra("Rivale")
    assert (rivale["giocatori"], rivale["residui"]) == (2, 35)


@pytest.mark.parametrize("giocatore, squadra, prezzo, errore", [
    ("a", "Rivale", 5, "appartiene già a Mia"),
    ("libero", "Rivale", 54, "al massimo 53"),
    ("libero", "Rivale", 0, "almeno 1"),
    ("libero", "Nessuna", 5, "non esiste"),
])
def test_aggiudica_rifiuta_operazioni_non_valide(lega, giocatore, squadra, prezzo, errore):
    with pytest.raises(ErroreMercato, match=errore):
        aggiudica(giocatore, squadra, prezzo)


def test_aggiudica_rifiuta_rosa_completa(lega):
    salva_regole(max_giocatori=2)
    with pytest.raises(ErroreMercato, match="rosa completa"):
        aggiudica("libero", "Mia", 5)


def test_svincolo_rimborsa_meta_se_ancora_in_serie_a(lega):
    messaggio = svincola("a")

    assert "50 crediti restituiti" in messaggio
    mia = _squadra("Mia")
    # 550 - 30 ancora in rosa - (100 - 50) persi con lo svincolo.
    assert (mia["giocatori"], mia["persi_svincoli"], mia["residui"]) == (1, 50, 470)


def test_svincolo_rimborso_pieno_se_ha_lasciato_la_serie_a(lega):
    assert [g["in_serie_a"] for g in rosa_squadra("Mia")] == [True, False]

    messaggio = svincola("estero")

    assert "30 crediti restituiti" in messaggio
    assert _squadra("Mia")["residui"] == 450


def test_annulla_ripristina_acquisti_e_svincoli(lega):
    prima = _squadra("Mia")
    svincola("a")
    aggiudica("libero", "Mia", 10)

    assert "acquisto di Delta" in annulla_ultimo()
    assert "svincolo di Alfa" in annulla_ultimo()

    dopo = _squadra("Mia")
    assert (dopo["giocatori"], dopo["residui"]) == (prima["giocatori"], prima["residui"])
    assert [m["annullato"] for m in storico_movimenti()] == [True, True]

    with pytest.raises(ErroreMercato, match="Non ci sono operazioni"):
        annulla_ultimo()


def test_annulla_svincolo_bloccato_se_giocatore_ripreso(lega):
    svincola("a")
    aggiudica("libero", "Rivale", 5)
    annulla_ultimo()  # annulla l'acquisto di Delta
    aggiudica("a", "Rivale", 5)

    annulla_ultimo()  # annulla l'acquisto di Alfa da parte del Rivale
    assert "svincolo di Alfa" in annulla_ultimo()
    assert _squadra("Mia")["giocatori"] == 2
