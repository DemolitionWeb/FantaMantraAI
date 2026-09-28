from engine.role_engine import (
    normalizza_ruoli,
    giocatore_compatibile,
)


def main():
    ruoli = "DC, DD"

    print("Ruoli:", normalizza_ruoli(ruoli))

    print(
        "DC:",
        giocatore_compatibile(ruoli, "DC")
    )

    print(
        "DD:",
        giocatore_compatibile(ruoli, "DD")
    )

    print(
        "DS:",
        giocatore_compatibile(ruoli, "DS")
    )


if __name__ == "__main__":
    main()