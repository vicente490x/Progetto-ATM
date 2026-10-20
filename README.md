# ATM didattico — pagina, PostgreSQL e TIBCO BW 6

Questa è una demo per l'esame: una pagina HTML/CSS/JavaScript invia la richiesta a un servizio Node/Express. Il servizio usa PostgreSQL per verificare cliente, PIN e disponibilità, prenota l'importo e scrive un XML in [input/](input). TIBCO BW 6 legge il file, conclude il prelievo nel database e lo sposta in [processed/](processed) o [error/](error). Il popup della pagina conferma **solo che il file è stato salvato**, non che TIBCO abbia già terminato.

## Preparazione

1. Servono Node.js, PostgreSQL con il database `atm_didattico`, TIBCO BusinessWorks 6 e Business Studio. Il processo completo generato è [ATMCompleto.bwp](ProgettoATM/Processes/progettoatm/ATMCompleto.bwp); il tuo [Process.bwp](ProgettoATM/Processes/progettoatm/Process.bwp) iniziale rimane intatto. Apri e verifica il nuovo processo seguendo [la guida TIBCO](docs/TIBCO_BW6_SETUP.md).
2. In pgAdmin, nel Query Tool di `atm_didattico`, esegui [01_creazione_tabelle.sql](database/01_creazione_tabelle.sql), poi [02_funzioni_atm.sql](database/02_funzioni_atm.sql). Il primo script non azzera i saldi se ripetuto.
3. In PowerShell, dalla cartella del progetto:

   ```powershell
   npm.cmd install
   Copy-Item .env.example .env
   ```

4. Apri `.env` e imposta `ATM_DB_PASSWORD` con la password PostgreSQL usata localmente. Lascia `ATM_OUTPUT_DIR` sulla cartella `input` di questo progetto, oppure inserisci un percorso assoluto che sia **la stessa cartella letta dal File Poller**. `.env` è escluso dal repository.
5. Avvia il servizio:

   ```powershell
   npm.cmd start
   ```

6. Apri `http://127.0.0.1:3000`. Il servizio ascolta solo su `127.0.0.1` per impostazione predefinita.

Se `npm` in PowerShell segnala che `npm.ps1` è bloccato, usa proprio `npm.cmd` come negli esempi sopra.

## Prova con Mario Rossi

Usa `Mario`, `Rossi`, PIN `12345` e 50 €. Il saldo iniziale dello script è 500,00 €, salvo prelievi già effettuati. Dopo il clic, la pagina crea un UUID e il servizio prenota 5000 centesimi e salva un file `UUID.xml` in [input/](input). TIBCO deve elaborarlo e spostarlo in [processed/](processed). In pgAdmin verifica:

```sql
SELECT nome, cognome, saldo_centesimi FROM public.clienti WHERE pin = '12345';
SELECT id_richiesta, importo_centesimi, stato, creata_il, conclusa_il
FROM public.transazioni ORDER BY creata_il DESC LIMIT 10;
```

Con saldo iniziale 50000, un prelievo da 50 € completato lascia 45000 e la transazione risulta `ESEGUITA`. Puoi vederlo anche con il pulsante **Controlla stato TIBCO** nella pagina. Se TIBCO non è ancora configurato, la riga rimane `PRENOTATA`, il saldo contabile non cambia e la disponibilità è già ridotta di 5000 centesimi.

## Struttura della parte web

| File | Compito |
|---|---|
| [index.html](public/index.html) | Modulo accessibile con Nome, Cognome, PIN, radio 50/100/200 € e Altro importo |
| [style.css](public/style.css) | Layout responsive semplice |
| [app.js](public/app.js) | Validazione nel browser, invio API, messaggio e popup |
| [server.js](server.js) | API locale, accesso a PostgreSQL e salvataggio XML atomico tramite `.tmp` e rename |
| [atm.js](lib/atm.js) | Validazione lato server e generazione dell'XML |

Il frontend accetta importi con punto o virgola e fino a due decimali; nell'XML il separatore è sempre il punto. Il PIN resta una stringa, così `01234` mantiene lo zero iniziale. Il servizio non accetta nomi di file o percorsi dal browser: il nome è l'UUID della richiesta. Se la rete si interrompe, il browser riprova con lo stesso UUID. Saldo e prenotazioni sono in **un solo database**, PostgreSQL.

## Stati e recupero

- `PRENOTATA`: file creato, oppure prenotazione da completare dopo un errore di scrittura. Il frontend può riprovare con lo stesso ID.
- `ESEGUITA`: TIBCO ha scalato il saldo e registrato l'esito. Ripetere lo stesso ID restituisce `GIA_ELABORATA` a TIBCO senza un altro addebito.
- `RIFIUTATA`: TIBCO ha annullato una prenotazione non utilizzabile; la disponibilità torna libera.

Se il database è indisponibile, non viene dichiarato un successo. Se TIBCO non raggiunge il database o non riesce a spostare un file, l'XML resta in `input` e va verificato o riprovato con **lo stesso ID**. Prima di riavviare il File Poller, controlla i file rimasti e lo stato delle transazioni. Le richieste manuali devono avere nome `UUID.xml`; senza una prenotazione nel database, TIBCO le rifiuta con `NON_PRENOTATA`.

Per prove locali esegui `npm.cmd test`. Questo verifica validazione e formato XML; non sostituisce i test manuali di PostgreSQL e TIBCO descritti nella guida. Il 20/10/2026 il processo BW è stato avviato in Business Studio: quattro richieste con nome UUID sono arrivate in `processed` e quattro transazioni risultano `ESEGUITA` in PostgreSQL. Tramite API sono stati verificati anche saldo insufficiente (HTTP 409), ripetizione di una richiesta completata (`ESEGUITA`) e riuso dell'ID con importo diverso (HTTP 409): numero di transazioni e saldi sono rimasti invariati. In TIBCO sono stati verificati il rifiuto di un XML valido senza prenotazione e di un XML senza PIN: entrambi sono finiti in `error` senza addebito. È riuscito anche il retry TIBCO di un UUID già archiviato: il file è uscito da `input`, l'archivio è rimasto identico e non c'è stato un secondo addebito. I risultati effettivamente verificati sono registrati in [Casi_di_test_ATM.xlsx](Consegna_esame/Casi_di_test_ATM.xlsx). Il PIN in chiaro nell'XML è previsto solo dalla traccia didattica e non è adatto a un ATM reale.
