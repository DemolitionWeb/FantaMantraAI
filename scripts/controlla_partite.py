from db.database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT
        id,
        campionato,
        giornata,
        squadra_casa,
        squadra_trasferta,
        kickoff_utc,
        stato,
        gol_casa,
        gol_trasferta
    FROM partite
    ORDER BY kickoff_utc
""")

partite = cursor.fetchall()

print("Partite:", len(partite))
print()

for p in partite:
    print(
        p[0],
        "|",
        p[1],
        "|",
        p[2],
        "|",
        p[3],
        "-",
        p[4],
        "|",
        p[5],
        "|",
        p[6],
        "|",
        p[7],
        "-",
        p[8]
    )

conn.close()