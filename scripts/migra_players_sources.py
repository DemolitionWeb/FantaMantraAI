from db.database import (
    get_connection,
    salva_player_source
)

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT
        id,
        fonte,
        fonte_id
    FROM giocatori
    WHERE fonte = 'BBS'
    AND fonte_id IS NOT NULL
""")

giocatori = cursor.fetchall()

conn.close()

print("Giocatori BBS trovati:", len(giocatori))

for giocatore_id, fonte, fonte_id in giocatori:
    salva_player_source(
        giocatore_id,
        fonte,
        fonte_id
    )

print("Migrazione completata.")