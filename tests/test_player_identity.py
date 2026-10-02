import player_identity


class FakeConnection:
    def __init__(self, righe):
        self.righe = righe

    def execute(self, query, parametri):
        assert parametri == ("mario rossi",)
        return self

    def fetchall(self):
        return self.righe

    def close(self):
        pass


def test_trova_giocatore_per_nome_restituisce_profilo(monkeypatch):
    monkeypatch.setattr(
        player_identity,
        "get_connection",
        lambda: FakeConnection(
            [("id-1", "Mario Rossi", "Roma", "DC")]
        ),
    )

    assert player_identity.trova_giocatore_per_nome(" Mario Rossi ") == {
        "id": "id-1",
        "nome": "Mario Rossi",
        "squadra": "Roma",
        "ruoli_mantra": "DC",
    }


def test_trova_giocatore_per_nome_ignora_risultati_ambigui(monkeypatch):
    monkeypatch.setattr(
        player_identity,
        "get_connection",
        lambda: FakeConnection(
            [
                ("id-1", "Mario Rossi", "Roma", "DC"),
                ("id-2", "Mario Rossi", "Lazio", "A"),
            ]
        ),
    )

    assert player_identity.trova_giocatore_per_nome("Mario Rossi") is None
