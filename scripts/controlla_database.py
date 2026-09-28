from db.database import get_connection

conn = get_connection()
cursor = conn.cursor()

tabelle = [
    "giocatori",
    "rosa",
    "partite",
    "presenze",
    "player_sources"
]

for tabella in tabelle:
    cursor.execute(
        f"SELECT COUNT(*) FROM {tabella}"
    )
    totale = cursor.fetchone()[0]

    print(f"{tabella}: {totale}")

conn.close()