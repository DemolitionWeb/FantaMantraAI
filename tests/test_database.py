from db.database import get_connection

conn = get_connection()
cursor = conn.cursor()

print("===== DATABASE =====")

cursor.execute("SELECT COUNT(*) FROM giocatori")
print("Giocatori:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM rosa")
print("Rosa:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM partite")
print("Partite:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM presenze")
print("Presenze:", cursor.fetchone()[0])

print("\n===== PRESENZE PARTITA =====")

cursor.execute("""
    SELECT
        g.nome,
        g.squadra,
        p.minuti,
        p.titolare,
        p.voto,
        p.gol,
        p.assist
    FROM presenze p
    JOIN giocatori g
        ON g.id = p.giocatore_id
    WHERE p.partita_id = ?
    ORDER BY g.squadra, g.nome
""", (
    "7918390f-9735-4bc7-9d3e-2a0bba9e9da2",
))

for riga in cursor.fetchall():
    print(riga)

conn.close()