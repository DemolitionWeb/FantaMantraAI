import streamlit as st

from auction_engine import (
    crediti_rimanenti,
    percentuale_budget_speso,
    offerta_massima,
)

from ai_coach import crea_coach, chiedi_consiglio, costruisci_contesto_asta
from staff.roles import RUOLI_STAFF

from database import crea_rosa_vuota, aggiungi_giocatore, conta_ruoli

if "rosa" not in st.session_state:
    st.session_state.rosa = crea_rosa_vuota()


st.set_page_config(
    page_title="Fantamantra AI",
    page_icon="⚽",
    layout="wide",
)


st.title("⚽ Fantamantra AI")
st.subheader("Il tuo staff tecnico durante l'asta")

with st.expander("Conosci lo Staff"):
    for ruolo in RUOLI_STAFF:
        st.markdown(f"**{ruolo['nome']}** — {ruolo['compito']}")
        st.caption(f"Limite: {ruolo['limite']}")


# =========================
# DATI DELLA SQUADRA
# =========================

st.sidebar.header("💰 Budget")

budget_iniziale = st.sidebar.number_input(
    "Budget iniziale",
    min_value=1,
    value=500,
    step=1,
    key="budget_iniziale",
)

spesa_totale = int(st.session_state.rosa["costo"].sum())

st.sidebar.divider()

st.sidebar.header("👥 La mia rosa")

portieri = st.sidebar.number_input(
    "Portieri",
    min_value=0,
    value=0,
    step=1,
    key="portieri",
)

difensori = st.sidebar.number_input(
    "Difensori",
    min_value=0,
    value=0,
    step=1,
    key="difensori",
)

centrocampisti = st.sidebar.number_input(
    "Centrocampisti",
    min_value=0,
    value=0,
    step=1,
    key="centrocampisti",
)

trequartisti = st.sidebar.number_input(
    "Trequartisti",
    min_value=0,
    value=0,
    step=1,
    key="trequartisti",
)

attaccanti = st.sidebar.number_input(
    "Attaccanti",
    min_value=0,
    value=0,
    step=1,
    key="attaccanti",
)


crediti = crediti_rimanenti(
    budget_iniziale,
    spesa_totale,
)

percentuale = percentuale_budget_speso(
    budget_iniziale,
    spesa_totale,
)

massima = offerta_massima(
    budget_iniziale,
    spesa_totale,
)


# =========================
# RIEPILOGO
# =========================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Budget iniziale",
        budget_iniziale,
    )

with col2:
    st.metric(
        "Crediti spesi",
        spesa_totale,
    )

with col3:
    st.metric(
        "Crediti rimasti",
        crediti,
    )

with col4:
    st.metric(
        "Offerta massima teorica",
        massima,
    )

st.progress(
    min(percentuale / 100, 1.0),
    text=f"Budget utilizzato: {percentuale:.1f}%",
)

st.divider()


# =========================
# GIOCATORE IN ASTA
# =========================

st.header("🔨 Giocatore in asta")

col1, col2 = st.columns(2)

with col1:
    giocatore = st.text_input(
        "Nome giocatore",
        placeholder="Es. Lautaro Martinez",
        key="giocatore_in_asta",
    )

with col2:
    prezzo_attuale = st.number_input(
        "Prezzo attuale",
        min_value=0,
        value=0,
        step=1,
        key="prezzo_attuale",
    )


st.divider()


# =========================
# CONSIGLIO
# =========================

st.header("🧠 AI Coach")

if st.button("Chiedi consiglio", type="primary"):

    if not giocatore:
        st.warning("Inserisci prima il nome del giocatore.")

    else:
        contesto = costruisci_contesto_asta(
            budget_iniziale=budget_iniziale,
            spesa_totale=spesa_totale,
            crediti=crediti,
            percentuale=percentuale,
            portieri=portieri,
            difensori=difensori,
            centrocampisti=centrocampisti,
            trequartisti=trequartisti,
            attaccanti=attaccanti,
            giocatore=giocatore,
            prezzo_attuale=prezzo_attuale,
            massima=massima,
        )

        try:
            coach = crea_coach()
            consiglio = chiedi_consiglio(coach, contesto)

            st.success("Consiglio dell'AI Coach")
            st.write(consiglio)

        except Exception as errore:
            st.error(f"Errore AI Coach: {errore}")

            st.divider()

st.header("👥 La mia rosa")

with st.form("aggiungi_giocatore_form"):

    col1, col2 = st.columns(2)

    with col1:
        nuovo_giocatore = st.text_input(
            "Nome giocatore"
        )

        nuova_squadra = st.text_input(
            "Squadra"
        )

    with col2:
        nuovi_ruoli = st.text_input(
            "Ruoli Mantra",
            placeholder="Es. DC, DD"
        )

        nuovo_costo = st.number_input(
            "Costo d'acquisto",
            min_value=0,
            value=1,
            step=1,
        )

    aggiungi = st.form_submit_button(
        "➕ Aggiungi alla rosa"
    )

    if aggiungi:

        if not nuovo_giocatore:
            st.warning("Inserisci il nome del giocatore.")

        elif not nuova_squadra:
            st.warning("Inserisci la squadra.")

        elif not nuovi_ruoli:
            st.warning("Inserisci almeno un ruolo Mantra.")

        else:

            st.session_state.rosa = aggiungi_giocatore(
                st.session_state.rosa,
                nuovo_giocatore,
                nuova_squadra,
                nuovi_ruoli,
                nuovo_costo,
            )

            st.success(
                f"{nuovo_giocatore} aggiunto alla rosa!"
            )

            st.rerun()


if not st.session_state.rosa.empty:

    st.subheader("Giocatori acquistati")

    st.dataframe(
        st.session_state.rosa,
        use_container_width=True,
        hide_index=True,
    )

    conteggio_ruoli = conta_ruoli(st.session_state.rosa)

    st.subheader("📊 Copertura ruoli Mantra")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("POR", conteggio_ruoli["POR"])
        st.metric("DC", conteggio_ruoli["DC"])
        st.metric("DD", conteggio_ruoli["DD"])

    with col2:
        st.metric("DS", conteggio_ruoli["DS"])
        st.metric("B", conteggio_ruoli["B"])
        st.metric("E", conteggio_ruoli["E"])

    with col3:
        st.metric("M", conteggio_ruoli["M"])
        st.metric("C", conteggio_ruoli["C"])
        st.metric("W", conteggio_ruoli["W"])

    with col4:
        st.metric("T", conteggio_ruoli["T"])
        st.metric("A", conteggio_ruoli["A"])
        st.metric("PC", conteggio_ruoli["PC"])

else:

    st.info(
        "La tua rosa è ancora vuota."
    )
