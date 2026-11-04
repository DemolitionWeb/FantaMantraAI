import pandas as pd
import streamlit as st

from auction_engine import offerta_massima
from config import RUOLI_MANTRA
from db.database import crea_database
from db.lega import (
    riepilogo_squadre,
    rose_complete,
    svincolati,
    ultimo_aggiornamento_rose,
)
from stato_app import leggi_valore

st.set_page_config(
    page_title="La lega | Fantamantra AI",
    page_icon="🏆",
    layout="wide",
)

crea_database()

st.title("🏆 La lega")

budget = leggi_valore("budget_iniziale", 500)
dimensione_rosa = leggi_valore("dimensione_rosa", 25)
squadre = riepilogo_squadre(budget)

if not squadre:
    st.info(
        "Nessuna rosa importata. Metti listone e rose in `data/` e lancia "
        "`python -m scripts.importa_listone_rose`."
    )
    st.stop()

aggiornamento = ultimo_aggiornamento_rose()
st.caption(
    f"Budget {budget} crediti · rosa da {dimensione_rosa} giocatori "
    "(impostabili nella pagina principale)"
    + (f" · rose aggiornate al {aggiornamento[:10]}" if aggiornamento else "")
)

giocatori_in_rosa = pd.DataFrame(rose_complete())

tab_squadre, tab_rose, tab_svincolati = st.tabs(
    ["Squadre e crediti", "Rose", "Svincolati"]
)


# =========================
# SQUADRE E CREDITI
# =========================

with tab_squadre:
    conteggi = (
        giocatori_in_rosa.pivot_table(
            index="fantasquadra", columns="ruolo_classic",
            values="giocatore_id", aggfunc="count", fill_value=0,
        )
        if not giocatori_in_rosa.empty else pd.DataFrame()
    )

    righe = []
    for squadra in squadre:
        posti = max(dimensione_rosa - squadra["giocatori"], 0)
        reparti = conteggi.loc[squadra["squadra"]] if squadra["squadra"] in conteggi.index else {}
        righe.append({
            "Squadra": ("⭐ " if squadra["mia"] else "") + squadra["squadra"],
            "Giocatori": squadra["giocatori"],
            "P": int(reparti.get("P", 0)),
            "D": int(reparti.get("D", 0)),
            "C": int(reparti.get("C", 0)),
            "A": int(reparti.get("A", 0)),
            "Spesi": squadra["spesi"],
            "Residui": squadra["residui"],
            "Posti liberi": posti,
            "Offerta massima": offerta_massima(
                budget, squadra["spesi"], posti_da_riempire=posti
            ),
        })

    tabella = pd.DataFrame(righe).sort_values("Residui", ascending=False)
    st.dataframe(tabella, hide_index=True, width="stretch")

    oltre = [r["Squadra"] for r in righe if r["Giocatori"] > dimensione_rosa]
    if oltre:
        st.warning(
            f"{len(oltre)} squadre hanno più di {dimensione_rosa} giocatori: "
            "aggiorna \"Giocatori da acquistare in totale\" nella pagina "
            "principale, altrimenti posti liberi e offerta massima risultano 0."
        )

    st.caption(
        "Offerta massima: crediti residui meno 1 credito per ogni altro posto "
        "da riempire. È il rilancio più alto che quella squadra può fare."
    )


# =========================
# ROSE
# =========================

with tab_rose:
    nomi = [s["squadra"] for s in squadre]
    predefinita = next((i for i, s in enumerate(squadre) if s["mia"]), 0)
    scelta = st.selectbox("Squadra", nomi, index=predefinita)

    rosa = giocatori_in_rosa[giocatori_in_rosa["fantasquadra"] == scelta]
    st.dataframe(
        rosa.rename(columns={
            "nome": "Giocatore", "squadra": "Squadra", "ruolo_classic": "R",
            "ruoli_mantra": "Ruoli Mantra", "costo": "Costo",
            "qa_mantra": "Quotazione", "fvm_mantra": "FVM",
            "fanta_media": "Fantamedia", "presenze": "Presenze",
        })[["R", "Giocatore", "Squadra", "Ruoli Mantra", "Costo",
            "Quotazione", "FVM", "Fantamedia", "Presenze"]],
        hide_index=True,
        width="stretch",
    )


# =========================
# SVINCOLATI
# =========================

with tab_svincolati:
    liberi = pd.DataFrame(svincolati())

    filtro_1, filtro_2, filtro_3 = st.columns(3)
    with filtro_1:
        ruoli = st.multiselect("Ruoli Mantra", RUOLI_MANTRA)
    with filtro_2:
        club = st.multiselect("Squadra di Serie A", sorted(liberi["squadra"].unique()))
    with filtro_3:
        cerca = st.text_input("Cerca per nome")

    ordina = st.radio(
        "Ordina per", ["FVM", "Quotazione", "Fantamedia"], horizontal=True
    )

    if ruoli:
        liberi = liberi[liberi["ruoli_mantra"].fillna("").apply(
            lambda valore: any(r in valore.split(", ") for r in ruoli)
        )]
    if club:
        liberi = liberi[liberi["squadra"].isin(club)]
    if cerca:
        liberi = liberi[liberi["nome"].str.contains(cerca, case=False, regex=False)]

    colonna = {"FVM": "fvm", "Quotazione": "quotazione", "Fantamedia": "fanta_media"}[ordina]
    liberi = liberi.sort_values(colonna, ascending=False, na_position="last")

    st.caption(f"{len(liberi)} giocatori svincolati")
    st.dataframe(
        liberi.rename(columns={
            "nome": "Giocatore", "squadra": "Squadra", "ruolo_classic": "R",
            "ruoli_mantra": "Ruoli Mantra", "quotazione": "Quotazione",
            "fvm": "FVM", "fanta_media": "Fantamedia", "presenze": "Presenze",
        })[["R", "Giocatore", "Squadra", "Ruoli Mantra", "Quotazione",
            "FVM", "Fantamedia", "Presenze"]],
        hide_index=True,
        width="stretch",
    )
