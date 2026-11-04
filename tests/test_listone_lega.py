import shutil
import tempfile
from pathlib import Path

import pytest
from openpyxl import Workbook

import db.database as database
from db.lega import importa_rose, leggi_rose_xlsx, riepilogo_squadre, svincolati
from db.listone import importa_listone, leggi_listone_csv, nomi_compatibili


@pytest.mark.parametrize("primo, secondo, atteso", [
    ("Martinez L.", "Lautaro Martínez", True),
    ("Martinez L.", "J. Martínez", False),
    ("Martinez Jo.", "J. Martínez", True),
    ("Idzes", "J. Idzes", True),
    ("Esposito Se.", "S. Esposito", True),
    ("Esposito F.P.", "S. Esposito", False),
    ("Skorupski", "Ł. Skorupski", True),
    ("Van Der Brempt", "I. Van der Brempt", True),
    ("Bernardeschi", "Federico Bernardeschi", True),
    ("Barella", "Bastoni", False),
])
def test_nomi_compatibili(primo, secondo, atteso):
    assert nomi_compatibili(primo, secondo) is atteso


def _riga_listone(fid, nome, ruolo, mantra, squadra, fvm):
    # Stesso formato del CSV esportato: 22 colonne, nessuna intestazione.
    return (f"{fid},{nome},{nome},{ruolo},{mantra},5,6,5,6,{squadra},"
            f"{fvm},{fvm},,,,https://img/{fid}.png,0,6.5,7.1,9,27,21")


@pytest.fixture
def ambiente(monkeypatch):
    cartella = Path(tempfile.mkdtemp(prefix="fantamantra-test-"))
    monkeypatch.setattr(database, "DB_PATH", cartella / "test.db")
    database.crea_database()
    yield cartella
    shutil.rmtree(cartella, ignore_errors=True)


def _scrivi_listone(cartella, righe):
    percorso = cartella / "listone.csv"
    percorso.write_text("\n".join(righe) + "\n", encoding="utf-8")
    return percorso


LISTONE_BASE = [
    _riga_listone(2764, "Martinez L.", "A", "PC", "Inter", 350),
    _riga_listone(2001, "Martinez Jo.", "P", "POR", "Inter", 20),
    _riga_listone(4431, "Carnesecchi", "P", "POR", "Atalanta", 30),
    _riga_listone(6024, "Sulemana I.", "C", "M;C", "Sassuolo", 12),
    _riga_listone(5585, "Malen", "A", "PC", "AS Roma", 420),
]


def test_leggi_listone_normalizza_squadra_e_ruoli(ambiente):
    giocatori = leggi_listone_csv(_scrivi_listone(ambiente, LISTONE_BASE))

    assert len(giocatori) == 5
    sulemana = giocatori[3]
    assert sulemana["ruoli_mantra"] == "M, C"
    assert sulemana["fvm_mantra"] == 12
    assert sulemana["fanta_media"] == 7.1
    assert giocatori[4]["squadra"] == "Roma"


def test_importa_listone_collega_e_unisce_doppioni(ambiente):
    conn = database.get_connection()
    conn.executescript("""
        INSERT INTO giocatori (id, nome, squadra) VALUES
            ('Carnesecchi-Atalanta', 'Carnesecchi', 'Atalanta'),
            ('M. Carnesecchi-Atalanta', 'M. Carnesecchi', 'Atalanta'),
            ('J. Martínez-Inter', 'J. Martínez', 'Inter'),
            ('I. Sulemana-Atalanta', 'I. Sulemana', 'Atalanta');
        INSERT INTO rosa (giocatore_id, costo_acquisto)
            VALUES ('Carnesecchi-Atalanta', 39);
        INSERT INTO presenze (giocatore_id, partita_id, voto)
            VALUES ('M. Carnesecchi-Atalanta', 'p1', 6.5);
        INSERT INTO player_sources (giocatore_id, fonte, fonte_id)
            VALUES ('M. Carnesecchi-Atalanta', 'BBS', '99');
    """)
    conn.commit()
    conn.close()

    esito = importa_listone(_scrivi_listone(ambiente, LISTONE_BASE))

    assert esito["uniti"] == [("M. Carnesecchi", "Carnesecchi")]
    assert esito["collegati"] == 3
    assert esito["nuovi"] == 2

    conn = database.get_connection()
    presenza = conn.execute("SELECT giocatore_id FROM presenze").fetchone()[0]
    fonte_bbs = conn.execute(
        "SELECT giocatore_id FROM player_sources WHERE fonte = 'BBS'"
    ).fetchone()[0]
    portiere = conn.execute(
        "SELECT nome FROM giocatori WHERE id = 'J. Martínez-Inter'"
    ).fetchone()[0]
    trasferito = conn.execute(
        "SELECT squadra, ruoli_mantra FROM giocatori WHERE id = 'I. Sulemana-Atalanta'"
    ).fetchone()
    nel_listone = conn.execute("SELECT COUNT(*) FROM listone").fetchone()[0]
    conn.close()

    # La presenza e l'ID BBS passano alla riga della rosa, che resta.
    assert presenza == fonte_bbs == "Carnesecchi-Atalanta"
    # "J. Martínez" è il portiere, non Lautaro.
    assert portiere == "Martinez Jo."
    # Trasferito: la riga esistente viene aggiornata con la nuova squadra.
    assert trasferito == ("Sassuolo", "M, C")
    assert nel_listone == 5

    # Una seconda importazione non crea né unisce nulla.
    di_nuovo = importa_listone(_scrivi_listone(ambiente, LISTONE_BASE))
    assert (di_nuovo["nuovi"], di_nuovo["uniti"], di_nuovo["collegati"]) == (0, [], 5)


def _scrivi_rose(cartella, rose):
    """Stesso layout dell'esportazione: squadra | costo | colonna vuota."""
    foglio = Workbook()
    pagina = foglio.active
    for posizione, (squadra, giocatori) in enumerate(rose.items()):
        colonna = 1 + posizione * 3
        pagina.cell(1, colonna, squadra)
        pagina.cell(1, colonna + 1, "costo")
        for riga, (nome, costo) in enumerate(giocatori, start=2):
            pagina.cell(riga, colonna, nome)
            pagina.cell(riga, colonna + 1, costo)
        totale = len(giocatori) + 2
        pagina.cell(totale, colonna, "totale")
        pagina.cell(totale, colonna + 1, sum(c for _, c in giocatori))
    percorso = cartella / "rose.xlsx"
    foglio.save(percorso)
    return percorso


ROSE = {
    "Abraham Lincon": [("Carnesecchi", 39), ("Malen", 154)],
    "FCM CALCIO": [("Martinez L.", 85), ("Sconosciuto", 1)],
}


def test_leggi_rose_xlsx(ambiente):
    rose = leggi_rose_xlsx(_scrivi_rose(ambiente, ROSE))

    assert list(rose) == ["Abraham Lincon", "FCM CALCIO"]
    assert rose["Abraham Lincon"]["giocatori"] == [("Carnesecchi", 39), ("Malen", 154)]
    assert rose["FCM CALCIO"]["totale"] == 86


def test_importa_rose_riepilogo_e_svincolati(ambiente):
    conn = database.get_connection()
    conn.execute("INSERT INTO giocatori (id, nome, squadra) VALUES"
                 " ('Carnesecchi-Atalanta', 'Carnesecchi', 'Atalanta')")
    conn.execute("INSERT INTO rosa (giocatore_id) VALUES ('Carnesecchi-Atalanta')")
    conn.commit()
    conn.close()
    importa_listone(_scrivi_listone(ambiente, LISTONE_BASE))

    esito = importa_rose(_scrivi_rose(ambiente, ROSE))

    assert esito["mia"] == "Abraham Lincon"
    assert esito["giocatori"] == 3
    assert esito["non_trovati"] == [("FCM CALCIO", "Sconosciuto")]
    assert esito["totali_diversi"] == []

    riepilogo = {r["squadra"]: r for r in riepilogo_squadre(budget=500)}
    assert riepilogo["Abraham Lincon"]["mia"] is True
    assert riepilogo["Abraham Lincon"]["residui"] == 500 - 193

    liberi = svincolati()
    assert [g["nome"] for g in liberi] == ["Martinez Jo.", "Sulemana I."]
    assert [g["nome"] for g in svincolati("POR")] == ["Martinez Jo."]


def test_importa_rose_senza_listone_da_errore(ambiente):
    with pytest.raises(ValueError, match="listone"):
        importa_rose(_scrivi_rose(ambiente, ROSE))
