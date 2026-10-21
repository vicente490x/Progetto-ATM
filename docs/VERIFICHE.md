# Verifiche del branch tibco-only-no-rest

Data: 21 ottobre 2026.

## Esecuzione e risultati

[Esecuzione GitHub Actions 39643799067](https://github.com/vicente490x/Progetto-ATM/actions/runs/39643799067), conclusa con successo sulla revisione `493774204756ef8dfb936e5840fd24597bc552b2`.

| Ambito | Prove superate | Evidenza |
| --- | ---: | --- |
| PostgreSQL 16.15 reale e isolato | 16 | [database.json](evidenze/database.json), DB01–DB16 |
| Validazione XSD con più varianti | 1 | [database.json](evidenze/database.json), XSD01 |
| Chromium 134.0.6998.35 | 15 | [browser.json](evidenze/browser.json), FE01–FE15 |
| Totale | 32 | Workflow `.github/workflows/collaudo-atm.yml` |

La query SQL viene estratta direttamente da `ATMCompleto.bwp`. Le prove coprono addebito, saldo insufficiente, credenziali errate, stringhe SQL ostili, replay UUID, conflitti di cliente/importo, saldo esatto, vecchie prenotazioni, concorrenza, rollback, persistenza fra connessioni, nominativi Unicode, apostrofi, PIN con zero iniziale e importi decimali. Il database contiene soltanto dati sintetici del collaudo; il test rifiuta un database non vuoto.

I test browser eseguono la pagina reale con Playwright e filesystem OPFS reale. Il selettore della cartella viene sostituito e i file di esito in processed/error vengono predisposti dal test. Verificano validazione, XML, UUID, doppio invio, ricaricamento, stato pendente, riconoscimento degli esiti, errore di scrittura iniettato, focus da Nome a Cognome e assenza di overflow orizzontale a 375 px. Non verificano il picker del sistema operativo, i suoi permessi, l'accesso da smartphone o l'esecuzione di TIBCO.

Sono stati inoltre verificati localmente sintassi JavaScript, parsing XML/XSLT, collegamenti delle attività e presenza di una query JDBC con cinque parametri. Questi controlli statici non sostituiscono la validazione semantica di Business Studio.

## Documenti aggiornati

- [TAD](TAD_Architettura_Tecnica_ATM.docx): architettura, flusso XML, query JDBC, concorrenza, configurazione, migrazione e limiti del collaudo.
- [Casi di test](Casi_di_test_ATM.xlsx): tutti i 31 casi compilati, 18 superati e 13 bloccati. Ogni riga dichiara il proprio ambito e richiama le evidenze. I contatori sono formule; nessun successo storico della versione REST è riportato come prova della nuova versione.

I 32 controlli automatici e i 31 casi del documento hanno granularità diversa: un caso può richiamare più controlli e richiedere ulteriori prove integrate. La data nei casi bloccati indica la valutazione del blocco.

## Verifiche ancora necessarie

Casi bloccati: TC_01, TC_03, TC_14, TC_21, TC_22, TC_23, TC_24, TC_25, TC_26, TC_27, TC_29, TC_30, TC_31.

Occorre un ambiente con Business Studio/BusinessWorks per validare, compilare e avviare il progetto. Restano da provare il flusso pagina–File Poller–JDBC–archivio, il replay attraverso BW, il riavvio con input pendenti, il fallimento dell'archiviazione dopo commit e gli eventi create/modify sui file vuoti o parziali. Servono inoltre cartelle reali per picker e permessi, interruzione durante la scrittura e una condivisione UNC fra due computer.

Le verifiche SQL e browser parziali di questi casi sono riportate nell'Excel. Il progetto non è dichiarato collaudato end-to-end finché tali prove non vengono completate.
