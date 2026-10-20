# Processo TIBCO generato

Il processo operativo è [ATMCompleto.bwp](../ProgettoATM/Processes/progettoatm/ATMCompleto.bwp). [module.bwm](../ProgettoATM/META-INF/module.bwm) punta a `progettoatm.ATMCompleto`. [Process.bwp](../ProgettoATM/Processes/progettoatm/Process.bwp) è il processo iniziale conservato come riferimento.

## Attività inserite

```text
FilePoller
  ├─ nome UUID.xml valido → ParseXml
  │   ├─ XML valido → ConcludiPrelievo (JDBC Query)
  │   │   ├─ OK / GIA_ELABORATA → PrelievoOK → SpostaProcessed
  │   │   ├─ rifiuto → PrelievoRifiutato → AnnullaRifiutato → SpostaRifiutato
  │   │   ├─ conflitto → ConflittoID (file in input)
  │   │   └─ errore JDBC → ErroreDatabase (file in input)
  │   └─ XML non valido → AnnullaXmlNonValido → SpostaXmlNonValido
  └─ nome non valido → SpostaNomeNonValido
```

Le attività JDBC usano la risorsa già presente [ConnessionePostgres.jdbcResource](../ProgettoATM/Resources/progettoatm/ConnessionePostgres.jdbcResource). Le funzioni chiamate si trovano in [02_funzioni_atm.sql](../database/02_funzioni_atm.sql). Il servizio locale deve prenotare l'UUID **prima** che TIBCO possa completare il prelievo; un XML copiato a mano senza prenotazione riceve `NON_PRENOTATA`.

## Primo controllo in Business Studio

1. Chiudi la scheda `ATMCompleto.bwp` in Business Studio **senza salvare modifiche non tue**: il file sul disco è stato aggiornato. In Project Explorer seleziona `ProgettoATM`, premi **F5** e riapri `Processes → progettoatm → ATMCompleto.bwp`.
2. Attendi la validazione e apri **Problems**. Se restano errori, copia la prima riga completa e il nome dell'attività: serviranno per correggere il file, senza ricostruire il diagramma.
3. Apri `ConcludiPrelievo → Statement`: cinque `?`, cinque parametri, `p_id` VARCHAR e `p_importo` BIGINT. Dopo aver eseguito lo script SQL in pgAdmin usa **Fetch** per aggiornare l'output. Non usare **Execute Query** con dati reali: la funzione può scalare il saldo.
4. Verifica `SpostaProcessed` e i tre `Sposta...` verso `error`: `fromFileName` deve arrivare da `FilePoller/fileInfo/fullName`; `toFileName` deve includere il nome del file. `SpostaProcessed` consente la sostituzione dello stesso UUID già archiviato dopo che PostgreSQL ha restituito `GIA_ELABORATA`; gli spostamenti verso `error` non sovrascrivono file.
5. Il vecchio file di esempio si trova in `examples/prelievo_valido_da_input.xml`, fuori dalla cartella monitorata. Il processo finale accetta nomi `UUID.xml`.
6. Esegui la prova completa descritta nel [README](../README.md). Controlla il saldo in pgAdmin e lo stato nella pagina.

Il controllo automatico `python tools/check_tibco_process.py` verifica gli schemi XML locali, i prefissi delle variabili e i mapping XSLT. La validazione BWDesign non è stata possibile nell'installazione locale perché l'eseguibile non trova la directory Eclipse `studio/4.0/eclipse/plugins`. La verifica decisiva resta **Problems** e l'esecuzione in Business Studio.

## Collaudo del 20/10/2026

Business Studio non mostra errori di validazione. L'applicazione è partita e quattro richieste con nome UUID sono state spostate in `processed`; PostgreSQL mostra quattro transazioni `ESEGUITA`. Questo verifica il percorso di successo, non ancora tutti i rami di errore. Il messaggio `FileAlreadyExistsExceptionFault` relativo a `prelievo_valido.xml` proveniva dal vecchio esempio rimasto in `input`, mentre un file omonimo era già presente in `error`. L'esempio è stato conservato in `examples/prelievo_valido_da_input.xml`.

Il servizio HTTP ha restituito `409 Saldo insufficiente` per un importo superiore alla disponibilità; ripetendo un ID già completato con gli stessi dati ha restituito `ESEGUITA`, e con un importo diverso ha restituito `409` per conflitto. Prima e dopo queste prove il database conteneva quattro transazioni e 75000 centesimi di saldo complessivo. Queste tre prove riguardano il servizio e PostgreSQL: non dimostrano ancora i rami di rifiuto e retry del processo TIBCO. Gli esiti sono riportati in [Casi_di_test_ATM.xlsx](../Consegna_esame/Casi_di_test_ATM.xlsx).

Due prove successive hanno attraversato TIBCO: un XML valido con UUID non prenotato e un XML senza PIN. Entrambi sono passati da `input` a `error`. Il primo era conforme allo XSD, il secondo è stato rifiutato dallo XSD per PIN mancante; saldo e numero di transazioni non sono cambiati. Dopo il refresh e il riavvio del processo aggiornato, un XML già archiviato con lo stesso UUID è stato reinserito in `input`: TIBCO lo ha tolto da `input`, l'archivio in `processed` ha mantenuto lo stesso SHA256 e PostgreSQL è rimasto a quattro transazioni `ESEGUITA` e 75000 centesimi complessivi. Il retry non ha effettuato un secondo addebito.
