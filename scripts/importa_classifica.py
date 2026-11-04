"""Scarica la classifica di Serie A da football-data.org e la salva nel DB.

Uso (dalla cartella del progetto):
    python -m scripts.importa_classifica
"""

from api.football_data import get_classifica, trasforma_classifica
from db.classifica import leggi_classifica, salva_classifica
from db.database import crea_database


def main():
    crea_database()

    righe = trasforma_classifica(get_classifica())
    salvate = salva_classifica(righe)

    if not salvate:
        print("Nessuna riga ricevuta: classifica salvata invariata.")
        return

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


if __name__ == "__main__":
    main()
