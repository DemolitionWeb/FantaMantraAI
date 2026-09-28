import pandas as pd

from db.database import salva_giocatori, get_connection


FILE_ROSA = "data/la-banda-dei-palloni-gonfiati_abraham-lincon_rosa_2026-09-07.csv"


def importa_rosa():

    df = pd.read_csv(FILE_ROSA, sep=";")

    giocatori = []
    rosa = []

    for _, riga in df.iterrows():

        nome = str(riga["Nome"]).strip()
        squadra = str(riga["Squadra"]).strip()
        ruolo = str(riga["Ruolo"]).strip()

        giocatore_id = f"{nome}-{squadra}"

        # =========================
        # DATI GENERALI GIOCATORE
        # =========================

        giocatore = {
            "id": giocatore_id,
            "nome": nome,
            "squadra": squadra,
            "ruoli_mantra": ruolo,
            "posizione_generica": None,
            "numero_maglia": None,
        }

        giocatori.append(giocatore)

        # =========================
        # DATI DELLA NOSTRA ROSA
        # =========================

        rosa.append({
            "giocatore_id": giocatore_id,
            "costo_acquisto": riga["Costo d'acquisto"],
            "quotazione_attuale": riga["Quotazione Attuale"],
            "fvm": riga["FVMp"],
            "media_voto": riga["Media Voto"],
            "fanta_media": riga["Fanta Media"],
            "partite_giocate": riga["Partite Giocate (a voto)"],
            "prestito": riga["Prestito"],
        })

    # Salviamo i giocatori
    salva_giocatori(giocatori)

    # Salviamo i dati della rosa
    conn = get_connection()
    cursor = conn.cursor()

    for giocatore in rosa:
        cursor.execute(
            """
            INSERT OR REPLACE INTO rosa (
                giocatore_id,
                costo_acquisto,
                quotazione_attuale,
                fvm,
                media_voto,
                fanta_media,
                partite_giocate,
                prestito
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                giocatore["giocatore_id"],
                giocatore["costo_acquisto"],
                giocatore["quotazione_attuale"],
                giocatore["fvm"],
                giocatore["media_voto"],
                giocatore["fanta_media"],
                giocatore["partite_giocate"],
                giocatore["prestito"],
            ),
        )

    conn.commit()
    conn.close()

    print("Giocatori importati:", len(giocatori))
    print("Elementi rosa importati:", len(rosa))


if __name__ == "__main__":
    importa_rosa()