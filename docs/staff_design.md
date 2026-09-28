# Lo Staff tecnico di Fantamantra AI

## La promessa

Lo Staff aiuta a prendere decisioni durante l'asta e, quando i dati lo
consentiranno, nella gestione della giornata. Ogni consiglio deve chiarire
quali elementi arrivano dai dati e quali sono valutazioni strategiche.

## I profili

### Head Coach — attivo
Coordina i pareri e restituisce una decisione pratica: acquistare, rilanciare
entro il tetto o passare. Riporta le incertezze che cambiano il consiglio.

### Direttore sportivo — attivo
Valuta un acquisto rispetto al prezzo corrente, al budget e ai ruoli già
presenti. Non presume obiettivi di rosa che l'utente non ha impostato.

### Responsabile budget — attivo
Usa i calcoli di auction_engine.py per spesa, crediti residui e offerta
massima. I numeri deterministici dell'app sono il limite del consiglio.

### Analista Mantra — parziale
Legge la copertura dei ruoli indicata nell'app. Può descrivere i conteggi, ma
per dichiarare una carenza deve prima conoscere il numero-obiettivo scelto
dall'utente per ogni ruolo o reparto.

### Scout — parziale
Valuta il giocatore soltanto sulle informazioni presenti nel contesto. Finché
la ricerca per nome non è collegata a un profilo verificato, non attribuisce
forma, titolarità o rendimento al calciatore.

### Allenatore tattico Matchday — in pausa
Confronta moduli e formazioni usando ruoli, disponibilità e presenze. Rimane
in pausa: lo storico attuale non è collegato alla maggior parte dei giocatori
della rosa.

### Analista disponibilità — in sviluppo
Riporta indisponibilità e fonte quando il record è disponibile. Un dato assente
non viene interpretato come conferma di idoneità e il ruolo non formula diagnosi.

## Come lavora lo Staff

1. L'app calcola budget e offerta massima.
2. L'utente fornisce prezzo, nome e composizione della rosa.
3. Il catalogo dei ruoli stabilisce per ogni specialista compiti e limiti.
4. Il Coach coordina i pareri con una sola richiesta al modello.
5. Il consiglio finale separa fatti, valutazioni e dati mancanti.

I cinque ruoli d'asta sono prospettive nella stessa consultazione; non sono
cinque agenti autonomi e non generano cinque chiamate API.

## Sequenza di sviluppo

1. Collegare il nome d'asta a un profilo giocatore con identificativo, fonte e
   confidence.
2. Aggiungere obiettivi configurabili per la rosa Mantra.
3. Riattivare il Matchday dopo aver collegato presenze sufficienti ai giocatori
   della rosa.
4. Passare allo Staff i dati di disponibilità con fonte e data di aggiornamento.
