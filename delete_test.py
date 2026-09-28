from db.database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute(
    "DELETE FROM partite WHERE id = ?",
    ("TEST-001",)
)

conn.commit()
conn.close()

print("Partita di test eliminata")