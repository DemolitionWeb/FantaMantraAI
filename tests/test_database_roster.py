import pandas as pd

from database import giocatore_esistente


def test_giocatore_esistente_ignora_maiuscole_e_spazi():
    rosa = pd.DataFrame(
        [
            {
                "giocatore": "  Giocatore Test ",
                "squadra": "Squadra Test",
                "ruoli": "DC",
                "costo": 10,
            }
        ]
    )

    assert giocatore_esistente(rosa, "giocatore test", " squadra test ")
    assert not giocatore_esistente(rosa, "Giocatore Test", "Altra Squadra")
