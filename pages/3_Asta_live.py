"""Asta dal vivo: la schermata dello Staff sul secondo dispositivo.

Sul primo dispositivo si chiama e si rilancia (Leghe Fantacalcio); qui si
vede subito chi è il giocatore, chi può permetterselo e il proprio tetto,
e si registrano aggiudicazioni e svincoli man mano che avvengono.
"""

import streamlit as st

from ai_coach import chiedi_consiglio, costruisci_contesto_asta, crea_coach
from db.database import crea_database
from db.lega import dati_listone, proprietario, rose_complete
from db.mercato import (
    ErroreMercato,
    aggiudica,
    annulla_ultimo,
    calcola_rimborso,
    elenco_listone,
    leggi_regole,
    rosa_squadra,
    salva_regole,
    situazione_squadre,
    storico_movimenti,
    svincola,
)
from engine.match_difficult import calcola_match_difficulty

st.set_page_config(
    page_title="Asta live | Fantamantra AI",
    page_icon="🔨",
    layout="centered",
)

crea_database()


def esegui(operazione, *argomenti, **opzioni):
    """Esegue un'operazione di mercato e mostra l'esito dopo il rerun."""
    try:
        st.session_state.esito_mercato = ("success", operazione(*argomenti, **opzioni))
    except ErroreMercato as errore:
        st.session_state.esito_mercato = ("error", str(errore))
    st.rerun()


st.title("🔨 Asta live")

esito = st.session_state.pop("esito_mercato", None)
if esito:
    getattr(st, esito[0])(esito[1])

regole = leggi_regole()
situazione = situazione_squadre(regole)

if not situazione:
    st.info(
        "Nessuna lega importata. Metti listone e rose in `data/` e lancia "
        "`python -m scripts.importa_listone_rose`."
    )
    st.stop()


# =========================
# REGOLE DELLA LEGA
# =========================

with st.expander("⚙️ Regole della lega"):
    with st.form("regole"):
        colonna_1, colonna_2 = st.columns(2)
        with colonna_1:
            budget = st.number_input("Budget iniziale", min_value=1,
                                     value=regole["budget_iniziale"], step=10)
            bonus = st.number_input("Bonus mercato di riparazione", min_value=0,
                                    value=regole["bonus_riparazione"], step=5,
                                    help="Consigliato: +50 per tutti (10% del budget).")
            massimo = st.number_input("Giocatori massimi per rosa", min_value=1,
                                      value=regole["max_giocatori"], step=1)
        with colonna_2:
            quota = st.number_input("Rimborso svincolo (%)", min_value=0, max_value=100,
                                    value=int(regole["quota_rimborso"] * 100), step=5,
                                    help="Chi ha lasciato la Serie A rimborsa sempre il 100%.")
            arrotondamento = st.radio(
                "Arrotondamento del rimborso", ["difetto", "eccesso"],
                index=0 if regole["arrotondamento"] == "difetto" else 1,
                help="Per difetto: pagato 5, rimborso 2. Per eccesso: 3.",
            )
        if st.form_submit_button("Salva regole"):
            salva_regole(budget_iniziale=budget, bonus_riparazione=bonus,
                         max_giocatori=massimo, quota_rimborso=quota / 100,
                         arrotondamento=arrotondamento)
            st.session_state.esito_mercato = ("success", "Regole salvate.")
            st.rerun()


# =========================
# LA MIA SITUAZIONE
# =========================

mia = next((s for s in situazione if s["mia"]), None)
if mia:
    st.caption(f"La tua squadra: **{mia['squadra']}**")
    colonne = st.columns(3)
    colonne[0].metric("Crediti residui", mia["residui"])
    colonne[1].metric("Posti liberi", mia["posti_liberi"])
    colonne[2].metric("Offerta massima", mia["offerta_massima"])
else:
    st.warning("La tua squadra non è stata individuata: reimporta le rose con --mia.")


# =========================
# GIOCATORE CHIAMATO
# =========================

st.subheader("Giocatore chiamato")

listone = elenco_listone()
indice = {g["giocatore_id"]: g for g in listone}
scelta = st.selectbox(
    "Giocatore",
    options=[g["giocatore_id"] for g in listone],
    format_func=lambda gid: (
        f"{indice[gid]['nome']} · {indice[gid]['squadra']} · {indice[gid]['ruoli_mantra']}"
    ),
    index=None,
    placeholder="Scrivi il nome per cercare…",
    label_visibility="collapsed",
)
prezzo = st.number_input("Prezzo attuale", min_value=0, step=1, key="prezzo_live")

if scelta:
    giocatore = indice[scelta]
    dati = dati_listone(scelta) or {}
    possessore = proprietario(scelta)

    valori = st.columns(4)
    valori[0].metric("Quotazione", dati.get("qa_mantra") if dati.get("qa_mantra") is not None else "—")
    valori[1].metric("FVM", dati.get("fvm_mantra") if dati.get("fvm_mantra") is not None else "—")
    valori[2].metric("Fantamedia", dati.get("fanta_media") or "—")
    valori[3].metric("Presenze", dati.get("presenze") if dati.get("presenze") is not None else "—")

    partita = calcola_match_difficulty(giocatore["squadra"])
    if partita and partita.get("difficulty_score") is not None:
        luogo = "in casa" if partita["casa_trasferta"] == "casa" else "in trasferta"
        st.caption(
            f"Prossima: vs {partita['avversario']} {luogo} · "
            f"difficoltà {partita['difficulty_score']:.0f}/100"
        )

    if possessore:
        st.warning(
            "È già nella tua rosa." if possessore["mia"]
            else f"Non è libero: appartiene a {possessore['squadra']} "
                 f"(pagato {possessore['costo']})."
        )
    else:
        # Chi può ancora rilanciare sopra il prezzo attuale.
        rivali = sorted(
            (s for s in situazione if not s["mia"] and s["offerta_massima"] > prezzo),
            key=lambda s: s["offerta_massima"], reverse=True,
        )
        if mia:
            if prezzo > mia["offerta_massima"]:
                st.error(f"Oltre il tuo tetto: puoi arrivare al massimo a {mia['offerta_massima']}.")
            else:
                st.success(f"Puoi rilanciare fino a {mia['offerta_massima']}.")

        if rivali:
            st.markdown(
                f"**Possono rilanciare sopra {prezzo}:** "
                + ", ".join(f"{s['squadra']} (fino a {s['offerta_massima']})" for s in rivali)
            )
        else:
            st.markdown(f"**Nessun avversario può superare {prezzo}.**")

        with st.form("aggiudica"):
            nomi = [s["squadra"] for s in situazione]
            predefinita = next((i for i, s in enumerate(situazione) if s["mia"]), 0)
            colonna_1, colonna_2 = st.columns([2, 1])
            vincitore = colonna_1.selectbox("Aggiudicato a", nomi, index=predefinita)
            prezzo_finale = colonna_2.number_input("Per", min_value=1, step=1,
                                                   value=max(prezzo, 1))
            if st.form_submit_button("✅ Aggiudica", type="primary"):
                esegui(aggiudica, scelta, vincitore, prezzo_finale)

        if st.button("🧠 Consiglio dello Staff"):
            miei = [g for g in rose_complete() if g["mia"]]
            profilo = {
                "nome": giocatore["nome"], "squadra": giocatore["squadra"],
                "ruoli_mantra": giocatore["ruoli_mantra"], "listone": dati,
                "rivali_che_possono_rilanciare": [
                    {"squadra": s["squadra"], "offerta_massima": s["offerta_massima"]}
                    for s in rivali
                ],
                "prossima_partita": partita,
            }
            contesto = costruisci_contesto_asta(
                budget_iniziale=regole["budget_iniziale"] + regole["bonus_riparazione"],
                spesa_totale=(mia["spesi"] + mia["persi_svincoli"]) if mia else 0,
                crediti=mia["residui"] if mia else 0,
                percentuale=0.0,
                portieri=sum(g["ruolo_classic"] == "P" for g in miei),
                difensori=sum(g["ruolo_classic"] == "D" for g in miei),
                centrocampisti=sum(g["ruolo_classic"] == "C" for g in miei),
                trequartisti=sum("T" in (g["ruoli_mantra"] or "").split(", ") for g in miei),
                attaccanti=sum(g["ruolo_classic"] == "A" for g in miei),
                giocatore=giocatore["nome"],
                prezzo_attuale=prezzo,
                massima=mia["offerta_massima"] if mia else 0,
                profilo_giocatore=profilo,
            )
            with st.spinner("Lo Staff sta valutando…"):
                try:
                    st.write(chiedi_consiglio(crea_coach(), contesto))
                except Exception as errore:
                    st.error(f"Errore AI Coach: {errore}")


# =========================
# SVINCOLI
# =========================

st.subheader("Svincoli")

nomi = [s["squadra"] for s in situazione]
predefinita = next((i for i, s in enumerate(situazione) if s["mia"]), 0)
squadra_svincolo = st.selectbox("Squadra", nomi, index=predefinita, key="squadra_svincolo")
rosa = rosa_squadra(squadra_svincolo)

if rosa:
    per_id = {g["giocatore_id"]: g for g in rosa}
    da_svincolare = st.selectbox(
        "Giocatore da svincolare",
        options=list(per_id),
        format_func=lambda gid: (
            f"{per_id[gid]['nome']} · {per_id[gid]['squadra']} · pagato {per_id[gid]['costo']}"
            + ("" if per_id[gid]["in_serie_a"] else " · non più in Serie A")
        ),
        index=None,
        placeholder="Scegli un giocatore…",
    )
    if da_svincolare:
        scelto = per_id[da_svincolare]
        uscito = st.checkbox(
            "Ha lasciato la Serie A (rimborso pieno)",
            value=not scelto["in_serie_a"],
            key=f"uscito_{da_svincolare}",
        )
        rimborso = calcola_rimborso(scelto["costo"] or 0, uscito, regole)
        st.caption(f"Rimborso: {rimborso} crediti su {scelto['costo']} pagati.")
        if st.button("Svincola", key="conferma_svincolo"):
            esegui(svincola, da_svincolare, uscito)
else:
    st.caption("Rosa vuota.")


# =========================
# STORICO
# =========================

st.subheader("Ultime operazioni")

movimenti = storico_movimenti()
if movimenti:
    for movimento in movimenti:
        testo = (
            f"{movimento['momento'][11:16]} · "
            + (f"**{movimento['giocatore']}** a {movimento['squadra']} per {movimento['costo']}"
               if movimento["tipo"] == "acquisto"
               else f"**{movimento['giocatore']}** svincolato da {movimento['squadra']}, "
                    f"+{movimento['rimborso']} crediti")
        )
        st.markdown(f"~~{testo}~~ (annullato)" if movimento["annullato"] else testo)
    if st.button("↩️ Annulla l'ultima operazione"):
        esegui(annulla_ultimo)
else:
    st.caption("Nessuna operazione registrata.")

st.divider()
st.caption(
    f"Regole: budget {regole['budget_iniziale']} + bonus {regole['bonus_riparazione']}, "
    f"massimo {regole['max_giocatori']} giocatori, rimborso svincolo "
    f"{regole['quota_rimborso']:.0%} per {regole['arrotondamento']} "
    "(100% se il giocatore ha lasciato la Serie A)."
)
