from engine.matchday_engine import crea_matchday


def main():
    risultato = crea_matchday()

    print("=== PANCHINA ===")

    migliore = risultato["migliore"]

    if not migliore:
        print("Nessuna formazione disponibile.")
        return

    print(
        f"Modulo: {migliore['modulo']}"
    )

    print(
        f"Score medio: "
        f"{migliore['score_medio']}"
    )

    print()

    for ruolo, giocatori in risultato[
        "panchina"
    ].items():

        print(f"{ruolo}:")

        for giocatore in giocatori:
            print(
                f"  {giocatore['nome']} "
                f"({giocatore['score']})"
            )


if __name__ == "__main__":
    main()