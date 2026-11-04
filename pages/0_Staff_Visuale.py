from pathlib import Path
from html import escape
import json
import re

import streamlit as st
import streamlit.components.v1 as components

from ai_coach import costruisci_contesto_asta, crea_coach, chiedi_consiglio
from analytics.availability_engine import analizza_disponibilita, prossima_partita
from auction_engine import crediti_rimanenti, offerta_massima, percentuale_budget_speso
from database import carica_rosa
from player_identity import trova_giocatore_per_nome
from staff.roles import CATALOGO_STAFF
from db.database import crea_database
from db.lega import dati_listone, proprietario, rose_complete, svincolati
from db.mercato import situazione_squadre
from engine.match_difficult import calcola_match_difficulty
from stato_app import leggi_valore

st.set_page_config(
    page_title="Staff visuale | Fantamantra AI",
    page_icon="⚽",
    layout="wide",
)

crea_database()


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

    budget = leggi_valore("budget_iniziale", 500)
    spesa = int(st.session_state.rosa["costo"].sum())
    crediti = crediti_rimanenti(budget, spesa)
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

        dati = dati_listone(profilo["id"]) or {}
        valori = "".join(
            f"<span>{escape(etichetta)} <b>{escape(str(dati[chiave]))}</b></span>"
            for etichetta, chiave in (
                ("Quotazione", "qa_mantra"), ("FVM", "fvm_mantra"),
                ("Fantamedia", "fanta_media"), ("Presenze", "presenze"),
            )
            if dati.get(chiave) is not None
        )
        valori_html = f'<div class="profile-values">{valori}</div>' if valori else ""

        possessore = proprietario(profilo["id"])
        if possessore and possessore["mia"]:
            badge = '<span class="owner-badge owner-mine">Già tuo</span>'
        elif possessore:
            badge = (
                '<span class="owner-badge owner-taken">'
                f'{escape(possessore["squadra"])} · {possessore["costo"]}</span>'
            )
        else:
            badge = '<span class="owner-badge owner-free">Svincolato</span>'
        profilo_html = f"""
          <section class="live-player-profile" aria-label="Profilo giocatore verificato">
            <div class="profile-badge">{escape(iniziali)}</div>
            <div>
              <small>Profilo verificato</small>
              <strong>{escape(profilo['nome'])}</strong>
              <small>{escape(profilo['squadra'] or 'Squadra non disponibile')} · Ruoli: {escape(profilo['ruoli_mantra'] or 'non disponibili')}</small>
              <small>Disponibilità: {escape(stato_disponibilita)} · Prossima: {escape(prossima)}</small>
              {valori_html}
            </div>
            {badge}
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
    html = _sostituisci_blocco(html, "LEAGUE", sezione_lega())
    html = _sostituisci_blocco(html, "MATCHDAY", sezione_matchday())
    return html


def _sostituisci_blocco(html, nome, contenuto):
    """Sostituisce il testo tra <!-- STREAMLIT_<nome>_START --> e _END.

    Se non ci sono dati, resta il testo di riserva della pagina statica.
    """
    if not contenuto:
        return html
    schema = re.compile(
        rf"<!-- STREAMLIT_{nome}_START -->.*?<!-- STREAMLIT_{nome}_END -->",
        re.DOTALL,
    )
    return schema.sub(lambda _: contenuto, html, count=1)


def sezione_lega():
    """Tabella crediti delle squadre e migliori svincolati."""
    squadre = situazione_squadre()
    if not squadre:
        return ""

    righe = []
    for squadra in sorted(squadre, key=lambda s: s["residui"], reverse=True):
        posti = squadra["posti_liberi"]
        massima_squadra = squadra["offerta_massima"]
        classe = ' class="is-mine"' if squadra["mia"] else ""
        righe.append(
            f"<tr{classe}><td>{escape(squadra['squadra'])}</td>"
            f"<td>{squadra['giocatori']}</td><td>{squadra['residui']}</td>"
            f"<td>{posti}</td><td>{massima_squadra}</td></tr>"
        )

    migliori = "".join(
        f"<tr><td>{escape(g['nome'])}<small>{escape(g['squadra'])} · "
        f"{escape(g['ruoli_mantra'] or '')}</small></td>"
        f"<td>{g['fvm'] if g['fvm'] is not None else '—'}</td>"
        f"<td>{g['quotazione'] if g['quotazione'] is not None else '—'}</td></tr>"
        for g in svincolati()[:8]
    )

    return f"""
        <div class="league-layout">
          <div class="data-card">
            <h3>Crediti delle squadre</h3>
            <table class="data-table">
              <thead><tr><th>Squadra</th><th>Gioc.</th><th>Residui</th><th>Posti</th><th>Offerta max</th></tr></thead>
              <tbody>{''.join(righe)}</tbody>
            </table>
          </div>
          <div class="data-card">
            <h3>Migliori svincolati</h3>
            <table class="data-table">
              <thead><tr><th>Giocatore</th><th>FVM</th><th>Quot.</th></tr></thead>
              <tbody>{migliori}</tbody>
            </table>
          </div>
        </div>
    """


def sezione_matchday():
    """Prossima partita e difficoltà dei club della propria rosa."""
    miei = [g for g in rose_complete() if g["mia"]]
    if not miei:
        return ""

    giocatori_per_club = {}
    for giocatore in miei:
        giocatori_per_club.setdefault(giocatore["squadra"], []).append(giocatore["nome"])

    partite = []
    for club, nomi in giocatori_per_club.items():
        partita = calcola_match_difficulty(club)
        if partita:
            partite.append((partita, nomi))

    if not partite:
        return ""

    partite.sort(key=lambda voce: (voce[0]["difficulty_score"] is None,
                                   voce[0]["difficulty_score"] or 0))
    righe = []
    for partita, nomi in partite:
        punteggio = partita["difficulty_score"]
        if punteggio is None:
            classe, larghezza, valore = "difficulty-medium", 0, "—"
        else:
            classe = ("difficulty-easy" if punteggio < 40
                      else "difficulty-medium" if punteggio < 70
                      else "difficulty-hard")
            larghezza, valore = punteggio, f"{punteggio:.0f}"
        luogo = "in casa" if partita["casa_trasferta"] == "casa" else "in trasferta"
        quando = (partita["kickoff"] or "")[:16].replace("T", " ")
        righe.append(f"""
          <div class="difficulty-row">
            <div><strong>{escape(partita['squadra'])}</strong><small>{escape(', '.join(nomi))}</small></div>
            <div>
              <div class="difficulty-bar"><span class="{classe}" style="width: {larghezza}%"></span></div>
              <small>{escape(partita.get('reason') or '')}</small>
            </div>
            <div class="difficulty-score">{valore}<small> · vs {escape(partita['avversario'])} {luogo}<br>{escape(quando)} UTC</small></div>
          </div>""")

    return f'<div class="difficulty-list">{"".join(righe)}</div>'


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
        if "rosa" not in st.session_state:
            st.session_state.rosa = carica_rosa()
        rosa = st.session_state.rosa
        spesa = int(rosa["costo"].sum())
        budget = leggi_valore("budget_iniziale", 500)
        crediti = crediti_rimanenti(budget, spesa)
        posti = max(leggi_valore("dimensione_rosa", 25) - len(rosa), 0)
        massima = offerta_massima(budget, spesa, posti_da_riempire=posti)
        contesto = costruisci_contesto_asta(
            budget_iniziale=budget,
            spesa_totale=spesa,
            crediti=crediti,
            percentuale=percentuale_budget_speso(budget, spesa),
            portieri=leggi_valore("portieri", 0),
            difensori=leggi_valore("difensori", 0),
            centrocampisti=leggi_valore("centrocampisti", 0),
            trequartisti=leggi_valore("trequartisti", 0),
            attaccanti=leggi_valore("attaccanti", 0),
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
