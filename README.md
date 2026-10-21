# Progetto ATM — TIBCO BusinessWorks 6

Il frontend HTML/CSS/JavaScript comunica con TIBCO tramite file XML locali. Non sono presenti server Node/Express, endpoint REST, agenti o accessi al database dal browser. Tutte le interrogazioni operative e le modifiche al database sono definite nell'attività JDBC `ConcludiPrelievo` di `ATMCompleto.bwp`; PostgreSQL conserva tabelle, vincoli e dati, senza funzioni applicative richieste dal progetto.

## Avvio

1. Importa in Business Studio `ProgettoATM` e `ProgettoATM.application` come progetti esistenti. Usa un workspace separato dalla cartella del repository.
2. Per una nuova installazione, esegui `database/01_creazione_tabelle.sql` nel database `atm_didattico`. Lo script non inserisce clienti di esempio e non modifica i saldi esistenti. Carica i clienti previsti dal tuo progetto.
3. Configura host, database, utente e password nella risorsa `ProgettoATM/Resources/progettoatm/ConnessionePostgres.jdbcResource`. La password non è distribuita nel repository. Installa il driver PostgreSQL nella tua installazione BW.
4. Crea le cartelle sorelle `input`, `processed`, `error`. In `ATMCompleto` configura File Poller con il percorso assoluto `.../input/*.xml`. Le destinazioni processed/error sono ricavate da quel percorso. Attiva create e modify events, includi file esistenti e contenuto testuale UTF-8. Imposta **Max Jobs = 1** per evitare processi contemporanei sullo stesso file.
5. Esegui **Validate** in Business Studio e avvia `ProgettoATM.application`. L'unico processo applicativo è `progettoatm.ATMCompleto`.
6. Apri `public/index.html` in Chrome/Edge desktop e premi **Collega cartella TIBCO**, scegliendo la cartella che contiene input/processed/error. Se il browser o le policy aziendali non consentono il picker da file locale, servi solo `public/` con un server statico su localhost o HTTPS. Il server statico non accede al database e non espone servizi applicativi.
7. Invia il prelievo e premi **Controlla stato TIBCO**. La pubblicazione del file non indica un addebito riuscito: il successo viene mostrato solo quando TIBCO archivia lo stesso XML in processed. In error il frontend mostra un rifiuto generico; il motivo è nel log TIBCO.

Questa interfaccia richiede una cartella condivisa con il runtime TIBCO e un browser con File System Access API. Non è una pagina remota utilizzabile da iPhone. Il browser richiede esplicitamente il permesso di accesso alla cartella.

## Migrazione dal branch main

Arresta il vecchio server e il vecchio processo prima di attivare questo branch. Risolvi prima tutte le prenotazioni `PRENOTATA` del vecchio flusso e archivia i vecchi input: non azzerare i saldi e non convertire automaticamente prenotazioni esistenti. Il nuovo processo blocca nuove richieste per un cliente che ha ancora prenotazioni pendenti.

Le vecchie funzioni PostgreSQL non sono più chiamate. Non vengono eliminate automaticamente dal database: la rimozione dei file dal repository non deve cancellare oggetti o dati del database esistente. Non avviare contemporaneamente la vecchia applicazione e questa versione.

## Gestione richieste

- UUID univoco per richiesta; dopo l'invio il modulo rimane bloccato fino a un esito.
- L'UUID viene conservato localmente anche dopo un ricaricamento; il PIN non viene salvato nel localStorage.
- Il File Poller ignora file temporaneamente vuoti e rileva le modifiche dopo la chiusura della scrittura del browser.
- Stessa richiesta già eseguita: nessun secondo addebito. Stesso UUID con cliente/importo diversi: rifiuto.
- Database non raggiungibile: file lasciato in input, nessun successo mostrato. Dopo il ripristino, riavvia il processo con Include Existing Files per riprovare lo stesso UUID.
- Scrittura o archiviazione fallita: verificare lo stesso UUID nel database e nelle cartelle, senza generarne un altro. Se la pubblicazione è fallita prima di creare l'XML, dopo aver escluso l'esistenza della transazione elimina solo la chiave `atm.pending` dal localStorage e ricarica la pagina.
- `processed` e `error` devono essere protette da modifiche esterne: costituiscono il riscontro locale dell'elaborazione. Il PIN negli XML è previsto dalla traccia del progetto.

## Documentazione e verifica

- [TAD aggiornato](docs/TAD_Architettura_Tecnica_ATM.docx)
- [Tabella dei 31 casi di test](docs/Casi_di_test_ATM.xlsx)
- [Architettura](docs/ARCHITETTURA.md) e [risultati ed evidenze](docs/VERIFICHE.md)

Il collaudo automatico ha superato 32 verifiche su PostgreSQL reale, XSD e Chromium. Nell'Excel sono compilati tutti i 31 casi: 18 superati nel perimetro dichiarato e 13 bloccati in attesa di runtime TIBCO, cartelle reali o infrastruttura di laboratorio. Le prove browser usano OPFS con picker sostituito ed esiti predisposti dal test; non costituiscono collaudo end-to-end BW.

I documenti Office originali in `docs/storico/` descrivono la versione precedente. I loro esiti non sono trasferiti a questo branch. Restano da eseguire importazione, validazione, build e collaudo integrato in Business Studio.
