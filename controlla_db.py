from db.database import get_connection

conn = get_connection()

print("Giocatori:", conn.execute(
    "SELECT COUNT(*) FROM giocatori"
).fetchone()[0])

print("Rosa:", conn.execute(
    "SELECT COUNT(*) FROM rosa"
).fetchone()[0])

conn.close()