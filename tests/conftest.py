"""Configurazione della raccolta pytest.

Alcuni file test_* sono script diagnostici manuali e fanno richieste HTTP
alla loro importazione. Restano disponibili per l'esecuzione diretta, ma non
devono essere eseguiti automaticamente durante la raccolta della suite.
"""


collect_ignore = [
    "test_convertitore.py",
    "test_match.py",
    "test_match_data.py",
    "test_sportmonks.py",
]
