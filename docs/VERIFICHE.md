# Verifiche del branch tibco-only-no-rest

Data: 21 ottobre 2026.

## Eseguite in questo ambiente

- Sintassi JavaScript: `node --check public/app.js` superata.
- Esecuzione del frontend con DOM e filesystem sostituiti da oggetti di test: validazione PIN, escape XML, conservazione dello zero iniziale, blocco del doppio invio, stato in attesa, conferma solo dopo processed, nuova richiesta esplicita. Superata. È un test isolato, non un collaudo browser–TIBCO.
- Parsing XML di BWP, XSD, configurazioni JDBC e modulo; parsing degli XSLT incorporati. Superato.
- Collegamenti del processo: dieci attività e nove transizioni, ciascuna con una sorgente e una destinazione. Superato.
- Una query JDBC parametrizzata, cinque parametri; nessuna chiamata alle vecchie funzioni PostgreSQL. Verificato staticamente.

## Non eseguite qui

Il runtime proprietario BW/Business Studio e PostgreSQL non sono disponibili in questo ambiente. Non è stata eseguita una build TIBCO né un'operazione reale sul database. I controlli XML non garantiscono la validazione semantica del modello BW.

Prima dell'utilizzo verificare su Business Studio:

1. Importazione, Validate, compilazione e avvio; compatibilità del flag modifyEvent e delle espressioni XPath con BW installato.
2. Selezione cartella da Chrome/Edge e permessi sul percorso effettivo.
3. Prelievo valido: un solo addebito, una transazione ESEGUITA, file in processed.
4. PIN errato, saldo insufficiente, XML non valido: nessun addebito; rifiuto visibile.
5. Stesso UUID e stessi dati: nessun secondo addebito. UUID con importo diverso: conflitto.
6. Due richieste superiori complessivamente al saldo: nessun saldo negativo; consistenza saldo/storico.
7. Database indisponibile e ripresa con stesso UUID; arresto dopo commit ma prima dell'archiviazione.
8. File temporaneamente vuoto durante la scrittura, errore di scrittura e ricaricamento del browser.
9. Richieste PRENOTATA della versione precedente: migrazione bloccata fino alla loro risoluzione.

Non sono stati marcati come superati casi nell'Excel storico. Lo storico documenta esclusivamente la vecchia versione.
