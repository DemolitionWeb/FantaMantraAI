from db.database import get_connection
from analytics.player_profile import crea_profilo


conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT giocatore_id
    FROM rosa
    LIMIT 1
""")

risultato = cursor.fetchone()

conn.close()

if not risultato:
    print("Nessun giocatore nella rosa.")
else:

    giocatore_id = risultato[0]

    profilo = crea_profilo(giocatore_id)

    analytics = profilo["analytics"]
    form = profilo["form"]
    partita = profilo["prossima_partita"]

    print()
    print("==========================================")
    print("PLAYER PROFILE")
    print("==========================================")

    print()
    print("GIOCATORE")
    print("Nome:", analytics["nome"])
    print("Squadra:", analytics["squadra"])
    print("Ruoli:", analytics["ruoli_mantra"])

    print()
    print("ANALYTICS")
    print("Presenze:", analytics["presenze"])
    print("Titolarità:", analytics["titolarita"], "%")
    print("Media minuti:", analytics["media_minuti"])
    print("Media voto:", analytics["media_voto"])
    print("Gol:", analytics["gol"])
    print("Assist:", analytics["assist"])

    print()
    print("FORMA")
    print("Form score:", form["form_score"])
    print("Media recenti:", form["media_voto_recenti"])
    print("Confidenza:", form["confidenza"], "%")

    print()
    print("PROSSIMA PARTITA")

    if partita:
        print(
            partita["casa"],
            "-",
            partita["trasferta"]
        )
        print("Kickoff:", partita["kickoff"])
    else:
        print("Nessuna partita trovata.")

    print()
    print("==========================================")