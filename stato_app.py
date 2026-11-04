"""Stato condiviso tra le pagine Streamlit.

Streamlit elimina dal session_state le chiavi dei widget non disegnati
nella pagina corrente: passando da una pagina all'altra budget e conteggi
tornerebbero ai valori iniziali. Il valore viene quindi copiato anche in
una chiave non legata al widget, che sopravvive al cambio pagina.
"""

import streamlit as st


def chiave_valore(chiave):
    return f"_valore_{chiave}"


def leggi_valore(chiave, predefinito):
    """Legge un valore impostato da input_persistente in qualsiasi pagina."""
    return st.session_state.get(
        chiave,
        st.session_state.get(chiave_valore(chiave), predefinito),
    )


def input_persistente(contenitore, etichetta, chiave, predefinito, min_value=0):
    if chiave not in st.session_state:
        st.session_state[chiave] = st.session_state.get(
            chiave_valore(chiave), predefinito
        )

    valore = contenitore.number_input(
        etichetta,
        min_value=min_value,
        step=1,
        key=chiave,
    )
    st.session_state[chiave_valore(chiave)] = valore
    return valore
