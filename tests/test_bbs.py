import requests

from config import BBS_API_KEY


if not BBS_API_KEY:
    print("❌ BBS_API_KEY non trovata nel file .env")
    raise SystemExit


url = "https://api.bigballsdata.com/v1/injuries"

headers = {
    "Authorization": f"Bearer {BBS_API_KEY}",
}

params = {
    "league": "seriea",
}


try:
    risposta = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=15,
    )

    print("STATUS CODE:", risposta.status_code)
    print()

    if risposta.status_code != 200:
        print("❌ ERRORE BIG BALLS")
        print(risposta.text)
        raise SystemExit

    dati = risposta.json()

    print("✅ INFORTUNI SERIE A TROVATI")
    print()

    print(dati)

except requests.RequestException as errore:
    print("❌ ERRORE DI CONNESSIONE")
    print(errore)