import argparse

from db.database import get_connection
from db.presenze import normalizza_nome, normalizza_squadra


def normalizza(valore):
    return normalizza_nome(valore)


def cognome(nome):
    parole = normalizza(nome).replace(".", " ").split()
    return parole[-1] if parole else ""


def trova_candidato(nome, squadra, rosa):
    nome_n, squadra_n = normalizza(nome), normalizza_squadra(squadra)
    esatti = [r for r in rosa if normalizza_squadra(r[2]) == squadra_n
              and normalizza(r[1]) == nome_n]
    if len(esatti) == 1:
        return esatti[0][0], "nome e squadra"
    if len(esatti) > 1:
        return None, "ambiguo: nome e squadra"

    surname = cognome(nome)
    if len(surname) < 3:
        return None, "nessuna corrispondenza sicura"
    possibili = [r for r in rosa if normalizza_squadra(r[2]) == squadra_n
                 and cognome(r[1]) == surname]
    if len(possibili) == 1:
        return possibili[0][0], "cognome univoco e squadra"
    if len(possibili) > 1:
        return None, "ambiguo: più giocatori con lo stesso cognome"
    return None, "nessuna corrispondenza"


def main():
    parser = argparse.ArgumentParser(
        description="Anteprima o riallineamento delle presenze ai giocatori della rosa."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="applica solo corrispondenze univoche senza conflitti",
    )
    args = parser.parse_args()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.id, g.nome, g.squadra, COUNT(p.id)
        FROM giocatori g
        JOIN presenze p ON p.giocatore_id = g.id
        GROUP BY g.id, g.nome, g.squadra
        ORDER BY g.nome
    """)
    sorgenti = cursor.fetchall()
    cursor.execute("""
        SELECT g.id, g.nome, g.squadra
        FROM rosa r JOIN giocatori g ON g.id = r.giocatore_id
    """)
    rosa = cursor.fetchall()

    aggiornamenti = []
    conflitti = []
    for source_id, nome, squadra, conteggio in sorgenti:
        target_id, motivo = trova_candidato(nome, squadra, rosa)
        if not target_id or target_id == source_id:
            print(f"{nome} | {squadra} | {conteggio} presenze | {motivo}")
            continue

        cursor.execute("""
            SELECT COUNT(*)
            FROM presenze src
            JOIN presenze dst
              ON dst.giocatore_id = ?
             AND dst.partita_id = src.partita_id
            WHERE src.giocatore_id = ?
        """, (target_id, source_id))
        collisioni = cursor.fetchone()[0]
        print(
            f"{nome} | {squadra} | {conteggio} presenze | "
            f"{source_id} -> {target_id} | {motivo}"
        )
        if collisioni:
            conflitti.append((source_id, target_id, collisioni))
        else:
            aggiornamenti.append((source_id, target_id))

    if not args.apply:
        print(f"Anteprima: {len(aggiornamenti)} riallineamenti applicabili.")
        conn.close()
        return

    if conflitti:
        print(f"Non applico: {len(conflitti)} corrispondenze hanno partite duplicate.")
        conn.close()
        return

    try:
        for source_id, target_id in aggiornamenti:
            cursor.execute(
                "UPDATE presenze SET giocatore_id = ? WHERE giocatore_id = ?",
                (target_id, source_id),
            )
            cursor.execute(
                "UPDATE player_sources SET giocatore_id = ? "
                "WHERE giocatore_id = ? AND fonte = 'BBS'",
                (target_id, source_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"Riallineati {len(aggiornamenti)} giocatori.")


if __name__ == "__main__":
    main()

