from engine.schierabilita_engine import calcola_schierabilita
from db.database import get_connection


def main():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, nome, squadra
        FROM giocatori
        ORDER BY nome
        LIMIT 10
        """
    )

    giocatori = cursor.fetchall()
    conn.close()

    print("=== SCHIERABILITA ===")

    for giocatore_id, nome, squadra in giocatori:
        risultato = calcola_schierabilita(giocatore_id)

        print()
        print(f"{nome} | {squadra}")
        print(f"Score: {risultato['score']}")
        print(f"Confidence: {risultato['confidence']}")
        print(f"Fattori: {risultato['fattori']}")
        print(
            f"Infortunato: "
            f"{risultato['disponibilita']['infortunato']}"
        )


if __name__ == "__main__":
    main()