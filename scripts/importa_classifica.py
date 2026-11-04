"""Scarica classifica e calendario di Serie A da football-data.org.

Uso (dalla cartella del progetto):
    python -m scripts.importa_classifica

Due richieste in tutto, ben dentro il limite del piano gratuito.
"""

from api.football_data import get_classifica, get_partite, trasforma_classifica
from db.calendario import adesso_utc, salva_calendario, trasforma_partite
from db.classifica import leggi_classifica, salva_classifica
from db.database import crea_database, get_connection


def main():
    crea_database()

    righe = trasforma_classifica(get_classifica())
    salvate = salva_classifica(righe)

    if not salvate:
        print("Nessuna riga ricevuta: classifica salvata invariata.")
    else:
        print(f"Righe di classifica salvate: {salvate}")
        print()
        print(f"{'Pos':>3}  {'Squadra':<18}{'Pt':>4}{'G':>4}{'GF':>5}{'GS':>5}{'DR':>5}")

        for riga in leggi_classifica("TOTAL"):
            print(
                f"{riga['posizione']:>3}  {riga['squadra']:<18}"
                f"{riga['punti']:>4}{riga['giocate']:>4}"
                f"{riga['gol_fatti']:>5}{riga['gol_subiti']:>5}"
                f"{riga['differenza_reti']:>5}"
            )

    nuove, aggiornate = salva_calendario(trasforma_partite(get_partite()))
    print()
    print(f"Calendario: {nuove} partite nuove, {aggiornate} aggiornate.")

    conn = get_connection()
    prossime = conn.execute(
        """
        SELECT giornata, squadra_casa, squadra_trasferta, kickoff_utc
        FROM partite
        WHERE stato = 'scheduled' AND kickoff_utc >= ?
        ORDER BY kickoff_utc
        LIMIT 10
        """,
        (adesso_utc(),),
    ).fetchall()
    conn.close()

    if prossime:
        print(f"Prossime partite (giornata {prossime[0][0]}):")
        for _, casa, trasferta, kickoff in prossime:
            print(f"  {kickoff[:16].replace('T', ' ')}  {casa} - {trasferta}")


if __name__ == "__main__":
    main()
