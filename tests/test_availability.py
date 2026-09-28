from analytics.availability_engine import analizza_disponibilita
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

    print("=== DISPONIBILITA ===")

    for giocatore_id, nome, squadra in giocatori:
        risultato = analizza_disponibilita(giocatore_id)

        print(
            f"{nome} | "
            f"{squadra} | "
            f"disponibile={risultato['disponibile']} | "
            f"infortunato={risultato['infortunato']}"
        )


if __name__ == "__main__":
    main()