from api.bigballs import (get_match, get_lineups, get_match_stats)
from db.presenze import trasforma_statistiche_partita
from db.database import salva_presenze  


MATCH_ID = "7918390f-9735-4bc7-9d3e-2a0bba9e9da2"

print("Scarico partita...")
partita = get_match(MATCH_ID)

print("Scarico lineup...")
lineups = get_lineups(MATCH_ID)

print("Scarico statistiche...")
statistiche = get_match_stats(MATCH_ID)

print("Trasformo i dati...")
presenze = trasforma_statistiche_partita(
    MATCH_ID,
    partita,
    lineups,
    statistiche
)

salva_presenze(presenze)
print("Presenze salvate nel database.")

print()
print("================================")
print("PRESENZE GENERATE:", len(presenze))
print("================================")

for presenza in presenze:
    print(
            presenza["giocatore_id"],
            "|",
            presenza["minuti"],
            "min",
            "|",
            presenza["voto"],
    )