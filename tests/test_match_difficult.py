from db.database import get_connection
from engine.match_difficult import calcola_match_difficulty


conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT squadra
    FROM giocatori
    WHERE squadra IS NOT NULL
    LIMIT 1
""")

risultato = cursor.fetchone()

conn.close()


print()
print("==========================================")
print("MATCH DIFFICULTY ENGINE")
print("==========================================")


if not risultato:
    print("Nessuna squadra disponibile.")

else:
    squadra = risultato[0]

    dati = calcola_match_difficulty(
        squadra
    )

    if not dati:
        print(
            "Nessuna partita programmata "
            "trovata per:",
            squadra
        )

    else:
        print("Squadra:", dati["squadra"])
        print("Avversario:", dati["avversario"])
        print(
            "Casa/Trasferta:",
            dati["casa_trasferta"]
        )
        print("Kickoff:", dati["kickoff"])
        print(
            "Difficulty:",
            dati["difficulty_score"]
        )
        print(
            "Confidence:",
            dati["confidence"]
        )
        print("Motivo:", dati["reason"])