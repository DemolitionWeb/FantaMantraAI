"""Importa listone e rose della lega dai file più recenti in data/.

Uso (dalla cartella del progetto):
    python -m scripts.importa_listone_rose
    python -m scripts.importa_listone_rose --mia "Abraham Lincon"

File cercati: data/listone_*.csv e data/rose_lega_*.xlsx (il più recente
per nome). Si possono indicare percorsi diversi con --listone e --rose.
"""

import argparse
from pathlib import Path

from db.database import crea_database
from db.lega import importa_rose, riepilogo_squadre, svincolati
from db.listone import importa_listone


CARTELLA_DATI = Path(__file__).resolve().parent.parent / "data"


def _piu_recente(schema):
    file = sorted(CARTELLA_DATI.glob(schema))
    return file[-1] if file else None


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--listone", type=Path, default=_piu_recente("listone_*.csv"))
    parser.add_argument("--rose", type=Path, default=_piu_recente("rose_lega_*.xlsx"))
    parser.add_argument("--mia", help="Nome della propria squadra nella lega")
    parser.add_argument("--budget", type=int, default=500)
    argomenti = parser.parse_args()

    if not argomenti.listone:
        parser.error("Nessun file data/listone_*.csv trovato.")

    crea_database()

    print(f"Listone: {argomenti.listone.name}")
    esito = importa_listone(argomenti.listone)
    print(f"  giocatori letti: {esito['letti']}")
    print(f"  collegati a giocatori esistenti: {esito['collegati']}")
    print(f"  nuovi: {esito['nuovi']}")
    print(f"  usciti dal listone: {esito['rimossi_dal_listone']}")
    if esito["uniti"]:
        print(f"  doppioni uniti: {len(esito['uniti'])}")
        for doppione, tenuto in esito["uniti"]:
            print(f"    {doppione} -> {tenuto}")

    if not argomenti.rose:
        print("\nNessun file data/rose_lega_*.xlsx trovato: rose non importate.")
        return

    print(f"\nRose: {argomenti.rose.name}")
    esito = importa_rose(argomenti.rose, argomenti.mia)
    print(f"  squadre: {esito['squadre']}, giocatori in rosa: {esito['giocatori']}")
    print(f"  la tua squadra: {esito['mia'] or 'non individuata (usa --mia)'}")
    for etichetta, chiave in (("non trovati nel listone", "non_trovati"),
                              ("nomi ambigui", "ambigui")):
        if esito[chiave]:
            print(f"  {etichetta}: {len(esito[chiave])}")
            for squadra, nome in esito[chiave]:
                print(f"    {squadra}: {nome}")
    for squadra, calcolato, nel_file in esito["totali_diversi"]:
        print(f"  ATTENZIONE {squadra}: spesa {calcolato}, totale nel file {nel_file}")

    print(f"\n{'Squadra':<24}{'Gioc.':>6}{'Spesi':>7}{'Residui':>9}")
    for riga in riepilogo_squadre(argomenti.budget):
        segno = " *" if riga["mia"] else ""
        print(f"{riga['squadra'] + segno:<24}{riga['giocatori']:>6}"
              f"{riga['spesi']:>7}{riga['residui']:>9}")

    liberi = svincolati()
    print(f"\nSvincolati: {len(liberi)}. I migliori per FVM Mantra:")
    for giocatore in liberi[:10]:
        print(f"  {giocatore['nome']:<22}{giocatore['squadra']:<12}"
              f"{giocatore['ruoli_mantra']:<10} FVM {giocatore['fvm']}")


if __name__ == "__main__":
    main()
