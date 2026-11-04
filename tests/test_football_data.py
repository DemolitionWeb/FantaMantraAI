import shutil
import tempfile
from pathlib import Path

import pytest

import config
import db.database as database
from api import football_data
from db.classifica import leggi_classifica, salva_classifica


# Struttura ridotta della risposta reale di /v4/competitions/SA/standings.
RISPOSTA_ESEMPIO = {
    "season": {"startDate": "2026-08-22", "currentMatchday": 11},
    "standings": [
        {
            "type": "TOTAL",
            "table": [
                {
                    "position": 1,
                    "team": {"id": 108, "name": "FC Internazionale Milano",
                             "shortName": "Inter", "tla": "INT"},
                    "playedGames": 10, "won": 8, "draw": 1, "lost": 1,
                    "points": 25, "goalsFor": 20, "goalsAgainst": 6,
                    "goalDifference": 14,
                },
                {
                    "position": 2,
                    "team": {"id": 100, "name": "AS Roma",
                             "shortName": "Roma", "tla": "ROM"},
                    "playedGames": 10, "won": 7, "draw": 2, "lost": 1,
                    "points": 23, "goalsFor": 15, "goalsAgainst": 7,
                    "goalDifference": 8,
                },
            ],
        },
        {
            "type": "HOME",
            "table": [
                {
                    "position": 1,
                    "team": {"id": 100, "name": "AS Roma",
                             "shortName": "Roma", "tla": "ROM"},
                    "playedGames": 5, "won": 5, "draw": 0, "lost": 0,
                    "points": 15, "goalsFor": 9, "goalsAgainst": 2,
                    "goalDifference": 7,
                },
            ],
        },
    ],
}


@pytest.fixture
def db_vuoto(monkeypatch):
    cartella = Path(tempfile.mkdtemp(prefix="fantamantra-test-"))
    monkeypatch.setattr(database, "DB_PATH", cartella / "test.db")
    database.crea_database()
    yield database
    shutil.rmtree(cartella, ignore_errors=True)


class RispostaFinta:
    def __init__(self, status_code=200, dati=None):
        self.status_code = status_code
        self.dati = dati or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self.dati


def test_trasforma_classifica_usa_nome_breve_e_tutti_i_tipi():
    righe = football_data.trasforma_classifica(RISPOSTA_ESEMPIO)

    assert len(righe) == 3
    inter = righe[0]
    assert inter["squadra"] == "Inter"
    assert inter["tipo"] == "TOTAL"
    assert (inter["gol_fatti"], inter["gol_subiti"]) == (20, 6)
    assert inter["stagione"] == "2026"
    assert inter["giornata"] == 11
    assert righe[2]["tipo"] == "HOME"


def test_nome_squadra_allineato_al_listone():
    assert football_data.nome_squadra({"shortName": "Como 1907"}) == "Como"
    assert football_data.nome_squadra({"shortName": "Venezia FC"}) == "Venezia"
    assert football_data.nome_squadra({"shortName": "Inter"}) == "Inter"
    assert football_data.nome_squadra({"name": "AS Roma"}) == "AS Roma"


def test_client_invia_la_chiave_nell_intestazione(monkeypatch):
    chiamate = {}

    def get_finto(url, headers, params, timeout):
        chiamate.update(url=url, headers=headers)
        return RispostaFinta(dati=RISPOSTA_ESEMPIO)

    monkeypatch.setattr(config, "FOOTBALL_DATA_API_TOKEN", "chiave-test")
    monkeypatch.setattr(football_data.requests, "get", get_finto)

    assert football_data.get_classifica() == RISPOSTA_ESEMPIO
    assert chiamate["url"].endswith("/v4/competitions/SA/standings")
    assert chiamate["headers"] == {"X-Auth-Token": "chiave-test"}


def test_client_senza_chiave_da_errore_chiaro(monkeypatch):
    monkeypatch.setattr(config, "FOOTBALL_DATA_API_TOKEN", None)

    with pytest.raises(ValueError, match="FOOTBALL_DATA_API_TOKEN"):
        football_data.get_classifica()


def test_client_segnala_limite_richieste(monkeypatch):
    monkeypatch.setattr(config, "FOOTBALL_DATA_API_TOKEN", "chiave-test")
    monkeypatch.setattr(football_data.requests, "get",
                        lambda *a, **k: RispostaFinta(status_code=429))

    with pytest.raises(RuntimeError, match="10 al minuto"):
        football_data.get_classifica()


def test_classifica_salvata_e_riletta_in_ordine(db_vuoto):
    salva_classifica(football_data.trasforma_classifica(RISPOSTA_ESEMPIO))

    totale = leggi_classifica("TOTAL")
    assert [r["squadra"] for r in totale] == ["Inter", "Roma"]
    assert [r["squadra"] for r in leggi_classifica("HOME")] == ["Roma"]


def test_classifica_vuota_non_cancella_quella_salvata(db_vuoto):
    salva_classifica(football_data.trasforma_classifica(RISPOSTA_ESEMPIO))

    assert salva_classifica([]) == 0
    assert len(leggi_classifica("TOTAL")) == 2
