from openai import OpenAI

from config import OPENAI_API_KEY
from staff.roles import costruisci_contesto_staff


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

