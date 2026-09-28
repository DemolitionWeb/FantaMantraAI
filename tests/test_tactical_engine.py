from engine.matchday_engine import crea_matchday


def main():
    risultato = crea_matchday()

    print("=== TACTICAL ENGINE ===")

    if not risultato["formazioni"]:
        print(
            "Nessuna formazione valutabile: mancano fattori di "
            "schierabilita basati su prestazioni."
        )
        return

    for formazione in risultato["formazioni"]:
        print()
        print(f"Modulo: {formazione['modulo']}")
        print(f"Score giocatori: {formazione['score_medio']}")
        print(f"Equilibrio: {formazione['equilibrio']}")
        print(f"Affidabilita: {formazione['affidabilita']}")
        print(f"Rischio: {formazione['rischio']}")
        print(f"SCORE FINALE: {formazione['score_finale']}")


if __name__ == "__main__":
    main()

