import streamlit as st

from staff.roles import CATALOGO_STAFF


st.set_page_config(
    page_title="Lo Staff | Fantamantra AI",
    page_icon="🧠",
    layout="wide",
)

st.title("Una squadra, cinque prospettive.")
st.subheader("Un solo obiettivo: aiutarti a decidere meglio all'asta.")
st.write(
    "Budget, ruoli e informazioni sul giocatore vengono letti da prospettive "
    "diverse e riuniti in un consiglio pratico. Ogni parere resta legato ai "
    "dati disponibili: quando un'informazione manca, lo Staff lo dice."
)
st.caption("Per tornare all'asta, seleziona la relativa voce nel menu di navigazione.")

staff_asta = [m for m in CATALOGO_STAFF if m["nel_consulto"]]
staff_matchday = [m for m in CATALOGO_STAFF if not m["nel_consulto"]]


def mostra_profili(profili):
    for inizio in range(0, len(profili), 2):
        colonne = st.columns(2)
        for colonna, membro in zip(colonne, profili[inizio:inizio + 2]):
            with colonna:
                with st.container(border=True):
                    st.markdown(f"### {membro['nome']}")
                    st.caption(f"Stato: {membro['stato']}")
                    st.write(membro["ruolo"])
                    st.markdown("**Dati utilizzati**")
                    st.write(membro["dati"])
                    st.caption(f"Limite: {membro['limite']}")


st.divider()
st.header("Staff d'asta")
st.write(
    "Questi cinque ruoli partecipano al consulto attuale. "
    "Sono competenze coordinate in una sola risposta, non cinque chiamate separate."
)
mostra_profili(staff_asta)

st.divider()
st.header("Area Matchday")
st.write(
    "Queste competenze completano lo Staff durante la stagione. "
    "Sono dichiarate separatamente perché i dati necessari non sono ancora "
    "collegati in modo sufficiente alla rosa."
)
mostra_profili(staff_matchday)

st.warning(
    "Lo Scout non riceve ancora un profilo statistico verificato dal nome "
    "digitato nell'asta. Il Matchday resta in pausa finché le presenze non "
    "coprono la rosa; l'analisi delle disponibilità non è ancora integrata "
    "nel consulto d'asta."
)

st.divider()
st.header("Come nasce il consiglio")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### 1 · Numeri certi")
    st.write("L'app calcola spesa, crediti residui e offerta massima.")
with col2:
    st.markdown("### 2 · Pareri distinti")
    st.write("Mantra, scouting e strategia considerano solo i dati forniti.")
with col3:
    st.markdown("### 3 · Una scelta")
    st.write("L'Head Coach sintetizza i pareri e indica comprare, rilanciare o passare.")

st.info(
    "L'offerta massima calcolata dall'app è un tetto: il consiglio non può "
    "superarlo. Le valutazioni strategiche sono separate dai dati e dai "
    "calcoli deterministici."
)
st.caption("Lo Staff cresce insieme ai dati disponibili e alle esigenze della tua rosa.")
