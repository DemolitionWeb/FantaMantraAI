from db.database import get_connection
from engine.schierabilità_engine import (
    calcola_schierabilita
)


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
print("SCHIERABILITÀ ENGINE")
print("==========================================")


for (giocatore_id,) in giocatori:

    dati = calcola_schierabilita(
        giocatore_id
    )

    print()
    print("Giocatore:", dati["nome"])
    print("Squadra:", dati["squadra"])
    print(
        "Schierabilità:",
        dati["schierabilita"]
    )
    print(
        "Confidenza:",
        dati["data_confidence"],
        "%"
    )

    print()
    print("FATTORI")

    for nome, valore in dati["fattori"].items():
        print(
            f"  {nome}: {valore}"
        )