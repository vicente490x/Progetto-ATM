# Architettura corrente

Browser → input → File Poller TIBCO → Parse XML → JDBC Query → log → processed/error → browser.

Il processo mantiene il formato nativo BWP e la risorsa JDBC del progetto. La pagina contiene solo validazione del formato, generazione XML e lettura dell'archivio. Non conosce credenziali JDBC, query o saldi.

`ConcludiPrelievo` contiene una query parametrizzata (UUID, nome, cognome, PIN, centesimi), senza stored procedure. Autentica il cliente, blocca la sua riga, controlla l'UUID e le vecchie prenotazioni, registra ESEGUITA o RIFIUTATA e addebita solo una transazione appena inserita. Inserimento e addebito sono una singola istruzione atomica. Il vincolo univoco sull'UUID impedisce duplicati. I rifiuti per saldo insufficiente restano registrati; credenziali errate e conflitti non sovrascrivono le transazioni.

Il frontend legge l'esito dell'archiviazione, senza visualizzare saldo o dettaglio del rifiuto. Questi dati sono disponibili nel processo/log. Il frontend non certifica un'erogazione fisica di denaro.

## Configurazione e limiti

- Un processo BW e una risorsa JDBC nel modulo esistente. Non viene introdotto un nuovo Shared Module o un sottoprocesso.
- PostgreSQL 12+ per MATERIALIZED CTE; conservati i vincoli dello schema esistente.
- Una sola istanza del File Poller e Max Jobs = 1. Create e modify events attivi. Gli XML temporaneamente vuoti vengono ignorati.
- Cartelle input, processed, error sorelle e accessibili dal browser e dal runtime. Permessi di scrittura riservati agli utenti del progetto.
- Nessun cliente precaricato, servizio Node, agente, generatore o dati di esecuzione versionati.
- TAD e tabella dei casi aggiornati in `docs/`: 32 verifiche automatiche superate, 18 casi superati e 13 bloccati nel perimetro dichiarato. Dettagli in [VERIFICHE.md](VERIFICHE.md). I documenti precedenti restano in storico.

## Riferimenti

- https://docs.tibco.com/pub/bwce/2.7.0/doc/html/binding-palette/file-poller.htm
- https://developer.chrome.com/docs/capabilities/web-apis/file-system-access
- https://www.postgresql.org/docs/current/sql-select.html
- https://www.postgresql.org/docs/current/transaction-iso.html
