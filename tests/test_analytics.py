from db.database import get_connection
from analytics.player_analytics import analizza_giocatore


conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT giocatore_id
    FROM presenze
    LIMIT 1
""")

risultato = cursor.fetchone()

conn.close()

if not risultato:
    print("Nessun giocatore disponibile.")
else:
    giocatore_id = risultato[0]

    dati = analizza_giocatore(giocatore_id)

    print()
    print("==============================")
    print("PLAYER ANALYTICS")
    print("==============================")

    for chiave, valore in dati.items():
        print(f"{chiave}: {valore}")