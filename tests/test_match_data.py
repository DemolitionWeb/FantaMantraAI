from api.bigballs import get_lineups, get_match_stats, get_match_events

MATCH_ID = "7918390f-9735-4bc7-9d3e-2a0bba9e9da2"


print("\n===== STRUTTURA LINEUPS =====")

lineups = get_lineups(MATCH_ID)

print("Tipo risposta:", type(lineups))
print("Chiavi principali:", lineups.keys())

if "data" in lineups:
    print("Chiavi data:", lineups["data"].keys())

    for squadra, giocatori in lineups["data"].items():
        print(f"\n{squadra}:")
        print("Tipo:", type(giocatori))
        print("Numero elementi:", len(giocatori) if isinstance(giocatori, list) else "N/D")

        if isinstance(giocatori, list) and giocatori:
            print("Primo elemento:")
            print(giocatori[0])


print("\n===== STRUTTURA STATS =====")

stats = get_match_stats(MATCH_ID)

print("Tipo risposta:", type(stats))
print("Chiavi principali:", stats.keys())

if "data" in stats:
    print("Chiavi data:", stats["data"].keys())

    for chiave, valore in stats["data"].items():
        print(f"\n{chiave}:")
        print("Tipo:", type(valore))

        if isinstance(valore, list):
            print("Numero elementi:", len(valore))

            if valore:
                print("Primo elemento:")
                print(valore[0])


print("\n===== STRUTTURA EVENTS =====")

events = get_match_events(MATCH_ID)

print("Tipo risposta:", type(events))
print("Chiavi principali:", events.keys())

if "data" in events:
    print("Tipo data:", type(events["data"]))

    if isinstance(events["data"], list):
        print("Numero eventi:", len(events["data"]))

        if events["data"]:
            print("Primo evento:")
            print(events["data"][0])
    else:
        print("Data:")
        print(events["data"])

        print("\n===== CONTROLLO LINEUP =====")

for squadra in ["home", "away"]:
    print(f"\n{squadra.upper()}")

    giocatori = lineups.get("data", {}).get(squadra, [])

    for giocatore in giocatori:
        print(
            giocatore.get("player_id"),
            "|",
            giocatore.get("name"),
            "|",
            giocatore.get("team_name"),
            "|",
            giocatore.get("starter")
        )