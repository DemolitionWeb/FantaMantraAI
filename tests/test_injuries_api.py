from pprint import pprint

from api.injuries import importa_infortuni


def main():
    risposta = importa_infortuni("seriea")

    print("\n=== RISPOSTA BBS ===")
    pprint(risposta, width=120)


if __name__ == "__main__":
    main()