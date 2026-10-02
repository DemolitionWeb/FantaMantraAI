from openai import OpenAI

from config import OPENAI_API_KEY
from staff.roles import costruisci_contesto_staff


def costruisci_contesto_asta(
    *,
    budget_iniziale,
    spesa_totale,
    crediti,
    percentuale,
    portieri,
    difensori,
    centrocampisti,
    trequartisti,
    attaccanti,
    giocatore,
    prezzo_attuale,
    massima,
):
    """Costruisce il contesto comune usato dalle pagine dell'asta."""
    return f"""
Sei il mio AI Coach durante un'asta di Fantacalcio Mantra.

DATI DELLA MIA SQUADRA
Budget iniziale: {budget_iniziale} crediti
Crediti già spesi: {spesa_totale}
Crediti rimasti: {crediti}
Percentuale budget spesa: {percentuale:.1f}%

COMPOSIZIONE DELLA ROSA
Portieri: {portieri}
Difensori: {difensori}
Centrocampisti: {centrocampisti}
Trequartisti: {trequartisti}
Attaccanti: {attaccanti}

GIOCATORE ATTUALMENTE IN ASTA
Nome: {giocatore}
Prezzo attuale: {prezzo_attuale} crediti
Offerta massima teorica: {massima}

Analizza la situazione e dammi un consiglio pratico su come comportarmi.
Considera prezzo, crediti rimasti, composizione della rosa, necessità del
reparto e rischio di spendere troppo presto.
Rispondi in modo sintetico e diretto.
"""


def crea_coach():
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY non configurata.")
    return OpenAI(api_key=OPENAI_API_KEY)


def chiedi_consiglio(coach, contesto):
    risposta = coach.responses.create(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "system",
                "content": (
                    "Coordini lo staff di una squadra di Fantacalcio Mantra "
                    "durante l'asta. Rispetta i compiti e i limiti di ogni ruolo. "
                    "Non inventare dati: se mancano statistiche del giocatore, "
                    "titolarità, obiettivi di rosa o informazioni sanitarie, "
                    "dillo chiaramente. L'offerta consigliata non può superare "
                    "l'offerta massima fornita. Scrivi in italiano, in modo "
                    "pratico e conciso, seguendo le cinque sezioni richieste."
                ),
            },
            {
                "role": "user",
                "content": costruisci_contesto_staff(contesto),
            },
        ],
    )
    return risposta.output_text

