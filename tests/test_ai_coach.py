from ai_coach import costruisci_contesto_asta


def test_costruisci_contesto_asta_include_dati_e_limiti():
    contesto = costruisci_contesto_asta(
        budget_iniziale=500,
        spesa_totale=120,
        crediti=380,
        percentuale=24,
        portieri=2,
        difensori=4,
        centrocampisti=5,
        trequartisti=2,
        attaccanti=3,
        giocatore="Giocatore Test",
        prezzo_attuale=35,
        massima=379,
    )

    assert "Giocatore Test" in contesto
    assert "Prezzo attuale: 35 crediti" in contesto
    assert "Offerta massima teorica: 379" in contesto
    assert "Budget iniziale: 500 crediti" in contesto
    assert "Rispondi in modo sintetico e diretto" in contesto
