import sqlite3

import pandas as pd

import database


def test_rosa_viene_salvata_e_ricaricata(tmp_path, monkeypatch):
    percorso_db = tmp_path / "rosa.db"
    monkeypatch.setattr(
        database,
        "get_connection",
        lambda: sqlite3.connect(percorso_db),
    )

    rosa_originale = pd.DataFrame(
        [
            {
                "giocatore": "Giocatore Test",
                "squadra": "Squadra Test",
                "ruoli": "DC, DD",
                "costo": 12,
            }
        ]
    )

    database.salva_rosa(rosa_originale)
    rosa_ricaricata = database.carica_rosa()

    pd.testing.assert_frame_equal(
        rosa_ricaricata.reset_index(drop=True),
        rosa_originale,
        check_dtype=False,
    )
