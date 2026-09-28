from db.database import get_connection
from analytics.form_engine import calcola_form


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
print("================================")
print("FORM ENGINE")
print("================================")

for (giocatore_id,) in giocatori:

    dati = calcola_form(giocatore_id)

    print()
    print("Giocatore:", giocatore_id)
    print("Partite:", dati["partite_recenti"])
    print("Media voto:", dati["media_voto_recenti"])
    print("Media minuti:", dati["media_minuti_recenti"])
    print("Gol:", dati["gol_recenti"])
    print("Assist:", dati["assist_recenti"])
    print("Form score:", dati["form_score"])
    print("Confidenza:", dati["confidenza"], "%")