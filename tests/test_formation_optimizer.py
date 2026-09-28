from engine.matchday_engine import crea_matchday


def main():
    risultato = crea_matchday()

    print("=== FORMATION OPTIMIZER ===")

    print(
        f"Giocatori analizzati: "
        f"{risultato['numero_giocatori']}"
    )

    print()

    for formazione in risultato["formazioni"]:

        print(
            f"MODULO: {formazione['modulo']} | "
            f"SCORE: {formazione['score_medio']}"
        )

        for assegnazione in formazione[
            "assegnazione"
        ]:
            giocatore = assegnazione["giocatore"]

            print(
                f"  {assegnazione['slot']} → "
                f"{giocatore['nome']} "
                f"({giocatore['score']})"
            )

        print()


if __name__ == "__main__":
    main()