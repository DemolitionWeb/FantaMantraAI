from engine.matchday_engine import crea_matchday


def main():
    risultato = crea_matchday()

    print("=== MATCHDAY ENGINE ===")
    print(
        f"Giocatori analizzati: "
        f"{risultato['numero_giocatori']}"
    )

    print()

    for giocatore in risultato["giocatori"]:
        print(
            f"{giocatore['nome']} | "
            f"{giocatore['squadra']} | "
            f"score={giocatore['score']} | "
            f"fascia={giocatore['fascia']} | "
            f"disponibile={giocatore['disponibile']} | "
            f"infortunato={giocatore['infortunato']}"
        )


if __name__ == "__main__":
    main()