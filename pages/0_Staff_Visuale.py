from pathlib import Path
from html import escape
import json

import streamlit as st
import streamlit.components.v1 as components

from ai_coach import costruisci_contesto_asta, crea_coach, chiedi_consiglio
from analytics.availability_engine import analizza_disponibilita, prossima_partita
from auction_engine import crediti_rimanenti, offerta_massima, percentuale_budget_speso
from database import carica_rosa
from player_identity import trova_giocatore_per_nome
from staff.roles import CATALOGO_STAFF

st.set_page_config(
    page_title="Staff visuale | Fantamantra AI",
    page_icon="⚽",
    layout="wide",
)


BASE_DIR = Path(__file__).resolve().parent.parent
HTML_PATH = BASE_DIR / "index.html"
CSS_PATH = BASE_DIR / "Style" / "style.css"
JS_PATH = BASE_DIR / "script.js"

ID_PROFILI = {
    "Head Coach": "coach",
    "Direttore sportivo": "sport-director",
    "Responsabile budget": "budget",
    "Analista Mantra": "mantra",
    "Scout": "scout",
}


def carica_prototipo() -> str:
    """Prepara il prototipo standalone per l'inclusione in Streamlit."""
    if "rosa" not in st.session_state:
        st.session_state.rosa = carica_rosa()

    budget = st.session_state.get("budget_iniziale", 500)
    spesa = int(st.session_state.rosa["costo"].sum())
    crediti = crediti_rimanenti(budget, spesa)
    massima = offerta_massima(budget, spesa)
    numero_giocatori = len(st.session_state.rosa)
    giocatore = escape(
        st.session_state.get("giocatore_in_asta", "")
        or "Nessun giocatore selezionato"
    )
    prezzo = st.session_state.get("prezzo_attuale", 0)
    ultimo_consiglio = st.session_state.get("ultimo_consiglio", "")
    profilo = st.session_state.get("profilo_giocatore")
    statistiche = f"""
      <section class="live-stats" aria-label="Riepilogo della squadra">
        <div class="live-stat"><strong>{budget}</strong><small>Budget iniziale</small></div>
        <div class="live-stat"><strong>{spesa}</strong><small>Crediti spesi</small></div>
        <div class="live-stat"><strong>{crediti}</strong><small>Crediti rimasti</small></div>
        <div class="live-stat"><strong>{numero_giocatori}</strong><small>Giocatori in rosa</small></div>
      </section>
    """
    asta = f"""
      <section class="live-auction" aria-label="Giocatore attualmente in asta">
        <div><small>Giocatore in asta</small><strong>{giocatore}</strong></div>
        <div><small>Prezzo attuale</small><span class="auction-price">{prezzo}</span></div>
      </section>
    """
    profilo_html = ""
    if profilo:
        try:
            disponibilita = analizza_disponibilita(profilo["id"])
            partita = prossima_partita(profilo["squadra"])
            stato_disponibilita = (
                "Non disponibile"
                if disponibilita.get("infortunato")
                else "Disponibile"
                if disponibilita.get("disponibile")
                else "Dato non disponibile"
            )
            prossima = (
                f"{partita['casa']} - {partita['trasferta']} · {partita['kickoff']}"
                if partita
                else "Nessuna partita programmata"
            )
        except Exception:
            stato_disponibilita = "Dato non disponibile"
            prossima = "Dato non disponibile"

        iniziali = "".join(
            parte[0] for parte in profilo["nome"].split()[:2] if parte
        ).upper()
        profilo_html = f"""
          <section class="live-player-profile" aria-label="Profilo giocatore verificato">
            <div class="profile-badge">{escape(iniziali)}</div>
            <div>
              <small>Profilo verificato</small>
              <strong>{escape(profilo['nome'])}</strong>
              <small>{escape(profilo['squadra'] or 'Squadra non disponibile')} · Ruoli: {escape(profilo['ruoli_mantra'] or 'non disponibili')}</small>
              <small>Disponibilità: {escape(stato_disponibilita)} · Prossima: {escape(prossima)}</small>
            </div>
          </section>
        """
    consiglio = ""
    if ultimo_consiglio:
        consiglio = f"""
          <section class="live-advice" aria-label="Ultimo consiglio dell'AI Coach">
            <p class="eyebrow">ULTIMO CONSIGLIO DELLO STAFF</p>
            <div class="live-advice-content">{escape(ultimo_consiglio)}</div>
          </section>
        """

    html = HTML_PATH.read_text(encoding="utf-8")
    css = CSS_PATH.read_text(encoding="utf-8")
    javascript = JS_PATH.read_text(encoding="utf-8")
    profili_staff = {
        ID_PROFILI[membro["nome"]]: {
            "title": membro["nome"],
            "description": membro["ruolo"],
            "limit": membro["limite"],
            "status": membro["stato"],
        }
        for membro in CATALOGO_STAFF
        if membro["nome"] in ID_PROFILI
    }

    html = html.replace(
        '<link rel="stylesheet" href="Style/style.css">',
        f"<style>{css}</style>",
    )
    html = html.replace(
        '<script src="script.js" defer></script>',
        "<script>window.staffProfiles = "
        + json.dumps(profili_staff, ensure_ascii=False)
        + f";</script><script>{javascript}</script>",
    )
    html = html.replace("<!-- STREAMLIT_LIVE_STATS -->", statistiche)
    html = html.replace("<!-- STREAMLIT_LIVE_AUCTION -->", asta)
    html = html.replace("<!-- STREAMLIT_PLAYER_PROFILE -->", profilo_html)
    html = html.replace("<!-- STREAMLIT_LIVE_ADVICE -->", consiglio)
    return html


st.caption("Prototipo visuale collegato all'applicazione Fantamantra AI")

st.subheader("Dati asta")
colonna_giocatore, colonna_prezzo = st.columns(2)
with colonna_giocatore:
    st.text_input(
        "Giocatore in asta",
        placeholder="Es. Lautaro Martinez",
        key="giocatore_in_asta",
    )
with colonna_prezzo:
    st.number_input(
        "Prezzo attuale",
        min_value=0,
        step=1,
        key="prezzo_attuale",
    )

profilo_giocatore = trova_giocatore_per_nome(
    st.session_state.get("giocatore_in_asta", "")
)
st.session_state.profilo_giocatore = profilo_giocatore

if st.button("Chiedi consiglio allo Staff", type="primary"):
    giocatore = st.session_state.get("giocatore_in_asta", "").strip()
    if not giocatore:
        st.warning("Inserisci prima il nome del giocatore.")
    else:
        rosa = st.session_state.get("rosa", carica_rosa())
        spesa = int(rosa["costo"].sum())
        budget = st.session_state.get("budget_iniziale", 500)
        crediti = crediti_rimanenti(budget, spesa)
        massima = offerta_massima(budget, spesa)
        contesto = costruisci_contesto_asta(
            budget_iniziale=budget,
            spesa_totale=spesa,
            crediti=crediti,
            percentuale=percentuale_budget_speso(budget, spesa),
            portieri=st.session_state.get("portieri", 0),
            difensori=st.session_state.get("difensori", 0),
            centrocampisti=st.session_state.get("centrocampisti", 0),
            trequartisti=st.session_state.get("trequartisti", 0),
            attaccanti=st.session_state.get("attaccanti", 0),
            giocatore=giocatore,
            prezzo_attuale=st.session_state.get("prezzo_attuale", 0),
            massima=massima,
            profilo_giocatore=profilo_giocatore,
        )
        prezzo = st.session_state.get("prezzo_attuale", 0)
        if prezzo > massima:
            st.error(
                f"Il prezzo attuale ({prezzo}) supera "
                f"l'offerta massima consentita ({massima})."
            )
        else:
            try:
                consiglio = chiedi_consiglio(crea_coach(), contesto)
                st.session_state.ultimo_consiglio = consiglio
                st.success("Consiglio dell'AI Coach")
            except Exception as errore:
                st.error(f"Errore AI Coach: {errore}")

components.html(carica_prototipo(), height=2100, scrolling=True)
