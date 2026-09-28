import requests

from config import SPORTMONKS_API_TOKEN


url = "https://api.sportmonks.com/v3/football/leagues"

headers = {
    "Authorization": SPORTMONKS_API_TOKEN,
}

risposta = requests.get(
    url,
    headers=headers,
    timeout=15,
)

print("STATUS CODE:", risposta.status_code)
print()

if risposta.status_code != 200:
    print("ERRORE:")
    print(risposta.text)
    raise SystemExit


dati = risposta.json()

print("CAMPIONATI DISPONIBILI:")
print("------------------------")

for lega in dati.get("data", []):
    print(
        "ID:",
        lega.get("id"),
        "| NOME:",
        lega.get("name"),
    )