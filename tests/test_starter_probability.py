from db.database import get_connection
from engine.starter_probability import calcola_starter_probability


conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT DISTINCT giocatore_id
    FROM presenze
    LIMIT 5
""")

giocatori = cursor.fetchall()

conn.close()


print()
print("==========================================")
print("STARTER PROBABILITY ENGINE")
print("==========================================")


for (giocatore_id,) in giocatori:

    dati = calcola_starter_probability(
        giocatore_id
    )

    print()
    print("Giocatore:", giocatore_id)
    print(
        "Starter probability:",
        dati["starter_probability"]
    )
    print(
        "Data confidence:",
        dati["data_confidence"],
        "%"
    )
    print(
        "Partite analizzate:",
        dati["partite_analizzate"]
    )
    print(
        "Titolarità storica:",
        dati["percentuale_titolarita"]
    )
    print(
        "Media minuti:",
        dati["media_minuti"]
    )