from db.database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    DELETE FROM presenze
    WHERE rowid NOT IN (
        SELECT MIN(rowid)
        FROM presenze
        GROUP BY giocatore_id, partita_id
    )
""")

conn.commit()

cursor.execute("SELECT COUNT(*) FROM presenze")
totale = cursor.fetchone()[0]

conn.close()

print("Presenze dopo pulizia:", totale)