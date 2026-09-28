from db.database import get_connection
from analytics.player_analytics import analizza_giocatore


def numero(valore, decimali=1):
    if valore is None:
        return "-"

    try:
        return f"{float(valore):.{decimali}f}"
    except (ValueError, TypeError):
        return str(valore)


conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT giocatore_id
    FROM rosa
""")

giocatori = cursor.fetchall()

conn.close()

print()
print("==========================================")
print("ANALYTICS ROSA")
print("==========================================")
print()

analizzati = 0

for (giocatore_id,) in giocatori:

    dati = analizza_giocatore(giocatore_id)

    if not dati:
        continue

    analizzati += 1

    nome = str(dati.get("nome") or "-")
    squadra = str(dati.get("squadra") or "-")

    titolarita = numero(dati.get("titolarita"), 1)
    minuti = numero(dati.get("media_minuti"), 1)
    voto = numero(dati.get("media_voto"), 2)

    gol = dati.get("gol") or 0
    assist = dati.get("assist") or 0

    print(
        f"{nome:<25} "
        f"{squadra:<18} "
        f"Tit: {titolarita:>5}% "
        f"Min: {minuti:>5} "
        f"Voto: {voto:>5} "
        f"G: {gol} "
        f"A: {assist}"
    )

print()
print("==========================================")
print("GIOCATORI IN ROSA:", len(giocatori))
print("GIOCATORI ANALIZZATI:", analizzati)
print("==========================================")