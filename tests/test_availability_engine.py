from analytics import availability_engine


class FakeCursor:
    def __init__(self, risultato):
        self.risultato = risultato
        self.query = None
        self.parametri = None

    def execute(self, query, parametri):
        self.query = query
        self.parametri = parametri

    def fetchone(self):
        return self.risultato


class FakeConnection:
    def __init__(self, risultato):
        self.cursoro = FakeCursor(risultato)

    def cursor(self):
        return self.cursoro

    def close(self):
        pass


def test_prossima_partita_restituisce_la_partita_programmata(monkeypatch):
    connessione = FakeConnection(
        ("match-1", "Roma", "Lazio", "2026-10-04T18:00:00Z", "scheduled")
    )
    monkeypatch.setattr(
        availability_engine,
        "get_connection",
        lambda: connessione,
    )

    risultato = availability_engine.prossima_partita("Roma")

    assert risultato == {
        "partita_id": "match-1",
        "casa": "Roma",
        "trasferta": "Lazio",
        "kickoff": "2026-10-04T18:00:00Z",
        "stato": "scheduled",
    }
    assert connessione.cursoro.parametri == ("Roma", "Roma")


def test_prossima_partita_senza_squadra_restituisce_none():
    assert availability_engine.prossima_partita("") is None
