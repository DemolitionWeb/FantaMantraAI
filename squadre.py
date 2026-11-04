"""Nomi canonici delle squadre.

Ogni fonte scrive le squadre a modo suo: BigBalls usa "AC Milan",
"AS Roma", "Inter Milan", football-data.org "Como 1907", "Venezia FC".
Il nome canonico è quello del listone Fantacalcio ("Milan", "Roma",
"Inter", "Como", "Venezia"): tutte le fonti vengono ricondotte a quello
prima di salvare o confrontare.

Le squadre non riconosciute (per esempio club esteri o nazionali)
restano invariate, salvo spazi superflui.
"""

import re
import unicodedata


# Squadre di Serie A con il nome usato dal listone. Comprende anche club
# spesso promossi, così le stagioni future non richiedono modifiche.
SQUADRE = (
    "Atalanta", "Bologna", "Cagliari", "Como", "Cremonese", "Empoli",
    "Fiorentina", "Frosinone", "Genoa", "Inter", "Juventus", "Lazio",
    "Lecce", "Milan", "Monza", "Napoli", "Palermo", "Parma", "Pisa",
    "Roma", "Salernitana", "Sampdoria", "Sassuolo", "Spezia", "Torino",
    "Udinese", "Venezia", "Verona",
)

# Forme diverse dal nome canonico anche dopo la normalizzazione.
ALIAS = {
    "inter milan": "Inter",
    "internazionale": "Inter",
    "internazionale milano": "Inter",
    "hellas verona": "Verona",
    "juve": "Juventus",
}

# Sigle societarie e parole che non identificano il club.
_PAROLE_SOCIETARIE = {
    "ac", "acf", "as", "bc", "bfc", "calcio", "cfc", "fc", "sc", "ss",
    "ssc", "uc", "us",
}

_CANONICI = None


def _normalizza(nome):
    testo = unicodedata.normalize("NFKD", str(nome)).casefold()
    testo = "".join(c for c in testo if not unicodedata.combining(c))
    testo = re.sub(r"[^a-z0-9]+", " ", testo)
    parole = [
        parola for parola in testo.split()
        if parola not in _PAROLE_SOCIETARIE and not re.fullmatch(r"\d{4}", parola)
    ]
    return " ".join(parole)


def nome_canonico(nome):
    """Nome della squadra come nel listone, o il nome originale se ignoto."""
    global _CANONICI

    if nome is None:
        return None

    originale = " ".join(str(nome).split())
    if not originale:
        return originale

    if _CANONICI is None:
        _CANONICI = {_normalizza(s): s for s in SQUADRE}

    chiave = _normalizza(originale)
    return _CANONICI.get(chiave) or ALIAS.get(chiave) or originale


def stessa_squadra(prima, seconda):
    """True se i due nomi indicano la stessa squadra."""
    if not prima or not seconda:
        return False
    return nome_canonico(prima) == nome_canonico(seconda)
