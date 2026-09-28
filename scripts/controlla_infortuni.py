from db.database import get_connection


def main():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            i.id,
            g.nome,
            g.squadra,
            i.fonte,
            i.fonte_id,
            i.stato,
            i.descrizione,
            i.ultimo_aggiornamento
        FROM infortuni i
        JOIN giocatori g
            ON g.id = i.giocatore_id
        ORDER BY g.squadra, g.nome
        """
    )

    risultati = cursor.fetchall()

    print(f"Infortuni nel database: {len(risultati)}")
    print()

    for riga in risultati:
        print(
            f"{riga[1]} | "
            f"{riga[2]} | "
            f"{riga[5]} | "
            f"{riga[6]}"
        )

    conn.close()


if __name__ == "__main__":
    main()