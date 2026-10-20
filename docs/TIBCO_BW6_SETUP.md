# Progetto ATM — guida completa per TIBCO BusinessWorks 6.8

Il processo completo è ora [ATMCompleto.bwp](../ProgettoATM/Processes/progettoatm/ATMCompleto.bwp) e il descrittore del modulo lo usa come componente attivo. Il tuo [Process.bwp](../ProgettoATM/Processes/progettoatm/Process.bwp) iniziale è stato conservato. Il nuovo processo è stato generato dai metadati BW 6.8 già presenti e controllato come XML; aprilo in Business Studio, verifica la vista **Problems** e completa la prova runtime. I passaggi sotto spiegano la configurazione delle attività e servono anche per correggere ciò che Business Studio potrebbe segnalare.

## 1. Cosa realizzerai

```text
Pagina web → servizio locale → prenotazione in PostgreSQL → input/UUID.xml
                                                         ↓
FilePoller → controllo nome → ParseXml + XSD → ConcludiPrelievo (JDBC Query)
                      errore XML ↓                     ↓
                         AnnullaPrenotazione       esito PostgreSQL
                                  ↓                 ↙              ↘
                                error/          processed/         error/
```

Il servizio salva l'XML e prenota l'importo. **TIBCO** esegue l'addebito: la funzione PostgreSQL aggiorna saldo e registro in una sola transazione. Il popup della pagina significa solo «richiesta salvata».

## 2. Prima di aprire il processo

1. In pgAdmin scegli `atm_didattico → Tools → Query Tool`.
2. Esegui [01_creazione_tabelle.sql](../database/01_creazione_tabelle.sql) se non lo hai già fatto.
3. Esegui tutto [02_funzioni_atm.sql](../database/02_funzioni_atm.sql). La scheda **Messages** deve mostrare `Query returned successfully` per ogni funzione.
4. Verifica che esistano le tre funzioni:

   ```sql
   SELECT proname FROM pg_proc
   WHERE proname IN ('prenota_prelievo','concludi_prelievo','annulla_prenotazione');
   ```

5. Controlla le cartelle [input/](../input), [processed/](../processed) ed [error/](../error). L'utente che avvia BW deve poter leggere e spostare file. Il servizio Node deve poter scrivere in `input`.
6. Usa solo dati fittizi. Il PIN in chiaro è un vincolo della traccia didattica; non inserirlo nei Log.

Nella cartella `input` c'è ancora [prelievo_valido.xml](../input/prelievo_valido.xml) dalle prove precedenti. Il nuovo flusso richiede un nome `UUID.xml`: prima della prova finale sposta quel file fuori da `input` oppure aspettati il ramo `NomeFileNonValido`. Conserva l'originale di esempio in [examples/](../examples).

**Non provare `concludi_prelievo` con l'ID di una richiesta vera mentre BW è in esecuzione:** la funzione addebita davvero il saldo di prova. Per i test usa UUID nuovi e controlla il database prima e dopo.

## 3. Controlla quello che hai già creato

Apri `ProgettoATM → Processes → progettoatm → Process.bwp`. Seleziona ogni attività e guarda **Properties** in basso.

1. **FilePoller → General:** `Filename = C:\Users\utente\Desktop\Progetto ATM\input\*.xml`; polling `5`; **Include Existing Files** attivo; **Exclude File Content** disattivo; **Content as = Text**, `UTF-8`.
2. **FilePoller → Advanced:** Create Events attivo, Modify/Delete disattivi, Include Sub-Directories disattivo. Non cambiare questi valori per le prove.
3. **ParseXml → General:** Input Style `Text`, **Validate Output** attivo, elemento globale `TransazioneATM` dello schema nel modulo. In **Input**, `xmlString` riceve `$FilePoller/fileContent/textContent`.
4. **ConnessionePostgres → General:** usa la risorsa già funzionante; driver `tibcosoftwareinc.jdbc.postgresql.PostgreSQLDriver`, URL `jdbc:tibcosoftwareinc:postgresql://localhost:5432;DatabaseName=atm_didattico`, utente che ha accesso alle tabelle e alle funzioni. Premi **Test Connection** solo se la configurazione è cambiata.
5. **LeggiClienti → Statement:** la query corrente con tre `?` deve avere tre parametri `p_nome`, `p_cognome`, `p_pin` nell'ordine; in **Input** mappa rispettivamente `Nome`, `Cognome`, `PIN` dell'output di ParseXml.

La tua query `LeggiClienti` è utile come esercizio di lettura. **Nel flusso finale, collega ParseXml direttamente a ConcludiPrelievo:** il controllo di saldo dentro LeggiClienti è solo informativo e non protegge due prelievi contemporanei. Puoi lasciare LeggiClienti nel diagramma come prova separata, ma non usare il suo ramo `ClienteSaldoOK` per spostare un file in `processed`.

**Correzione ora:** nel processo salvato il Log `ClienteSaldoOK` contiene «Saldo insufficiente», mentre il Log `SaldoInsufficiente` contiene «Cliente riconosciuto e saldo sufficiente». In **Input → message** scambia i due testi. In BW l'espressione di testo è fra apici, per esempio `'Saldo insufficiente'`.

## 4. Aggiungi il controllo del nome file

Il servizio crea nomi `UUID.xml`. L'UUID è la chiave della tabella `transazioni` e impedisce il doppio addebito.

1. Dalla Palette cerca **Log** e trascinalo tra FilePoller e ParseXml. Chiamalo `ControllaNomeFile`; messaggio `'File XML ricevuto'`.
2. Collega `FilePoller → ControllaNomeFile` con transizione **Success**.
3. Collega `ControllaNomeFile → ParseXml` con **Success with condition** e usa l'editor XPath:

   ```xpath
   matches($FilePoller/fileInfo/fileName,
     '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\.xml$')
   ```

4. Aggiungi un secondo Log `NomeFileNonValido` e collegalo da `ControllaNomeFile` con **Success with no matching condition**. Messaggio `'Nome file non valido: serve UUID.xml'`.
5. Da questo Log aggiungi un **Rename File** `SpostaNomeNonValido` verso `error` come descritto alla fase 8.

Nella tua versione, se l'albero XPath mostra un percorso leggermente diverso per `fileName`, trascina il campo dall'albero a sinistra dell'editor. Il File Poller BW 6.8 espone `fileInfo/fileName` e `fileInfo/fullName`.

## 5. Prepara il nuovo JDBC Query che esegue il prelievo

1. Nella Palette cerca **JDBC Query**, trascinalo dopo ParseXml e chiamalo `ConcludiPrelievo`.
2. Nella scheda **General** scegli la risorsa `ConnessionePostgres`. Imposta Timeout, per esempio `30` secondi, e Maximum Rows `1`.
3. In **Statement** incolla esattamente:

   ```sql
   SELECT esito, saldo_centesimi
   FROM public.concludi_prelievo(
     CAST(? AS UUID), ?, ?, ?, CAST(? AS BIGINT)
   )
   ```

4. Nella tabella **Prepared Statement** aggiungi **cinque** righe in questo ordine. Il numero delle righe deve coincidere con il numero dei `?`:

   | Nome | Tipo JDBC | Da dove arriva |
   |---|---|---|
   | `p_id` | VARCHAR | Nome del file senza `.xml` |
   | `p_nome` | VARCHAR | `ParseXml/Cliente/Nome` |
   | `p_cognome` | VARCHAR | `ParseXml/Cliente/Cognome` |
   | `p_pin` | VARCHAR | `ParseXml/Cliente/PIN` |
   | `p_importo` | BIGINT | Importo in centesimi |

5. Premi **Fetch** per aggiornare lo schema di output. Dovresti vedere `resultSet → Record → esito` e `saldo_centesimi`. **Execute Query** esegue la SELECT: usa solo dati di prova, perché questa SELECT chiama una funzione che può addebitare.
6. In **Input** mappa i cinque campi, usando l'albero a sinistra per i tre campi cliente. Per `p_id` usa:

   ```xpath
   substring-before($FilePoller/fileInfo/fileName, '.xml')
   ```

   Per `p_importo` usa:

   ```xpath
   xs:long($ParseXml/DettagliPrelievo/Importo * 100)
   ```

   Se Business Studio non riconosce `xs:long`, usa l'editor delle funzioni per convertire a intero lungo; non trasformare l'importo in `double`. Lo schema limita a due decimali.
7. Collega **ParseXml → ConcludiPrelievo** con **Success**. Prima disattiva o rimuovi la vecchia freccia ParseXml → LeggiClienti dal flusso principale, così non partono due percorsi concorrenti.

## 6. Gestisci gli esiti del database

Per leggere il campo `esito`, espandi nell'editor XPath l'output di ConcludiPrelievo. La forma di solito è `$ConcludiPrelievo/Record[1]/esito`; **usa il percorso inserito dall'editor** se la tua versione mostra un livello `resultSet` in più.

Da `ConcludiPrelievo` crea questi rami. Prima aggiungi il Log, poi seleziona la freccia e scegli **Properties → Condition Type**:

| Condizione | Log | Passo dopo il Log |
|---|---|---|
| `esito = 'OK' or esito = 'GIA_ELABORATA'` | `PrelievoOK`, testo `'Prelievo eseguito o già elaborato'` | `SpostaProcessed` |
| `esito = 'CLIENTE_NON_VALIDO' or esito = 'SALDO_INSUFFICIENTE' or esito = 'RIFIUTATA' or esito = 'NON_PRENOTATA'` | `PrelievoRifiutato`, testo `'Prelievo rifiutato'` | `AnnullaPrenotazione` e poi `SpostaRifiutato` |
| `esito = 'CONFLITTO_ID'` oppure nessun esito riconosciuto | `ConflittoID`, testo `'ID o dati non coerenti: verifica manuale'` | lascia il file in `input`, verifica la prenotazione |
| **Error** dell'attività JDBC | `ErroreDatabase`, testo `'Errore database: richiesta da verificare'` | lascia il file in `input` |

Per la prima riga usa **Success with condition**. Per l'ultima usa **Error**. Per il conflitto puoi usare **Success with no matching condition**, dopo aver creato le condizioni per successi e rifiuti. Il file con errore tecnico rimane in `input`: un errore JDBC non equivale a saldo insufficiente.

Per compilare le due condizioni principali, supponendo che l'editor XPath abbia creato `$ConcludiPrelievo/Record[1]/esito`, incolla:

```xpath
$ConcludiPrelievo/Record[1]/esito = 'OK'
or $ConcludiPrelievo/Record[1]/esito = 'GIA_ELABORATA'
```

```xpath
$ConcludiPrelievo/Record[1]/esito = 'CLIENTE_NON_VALIDO'
or $ConcludiPrelievo/Record[1]/esito = 'SALDO_INSUFFICIENTE'
or $ConcludiPrelievo/Record[1]/esito = 'RIFIUTATA'
or $ConcludiPrelievo/Record[1]/esito = 'NON_PRENOTATA'
```

Se l'editor inserisce `$ConcludiPrelievo/resultSet/Record[1]/esito`, sostituisci **l'intero percorso** in tutte le righe. Controlla anche che ci sia esattamente un `Record` prima di scegliere un esito; la funzione SQL restituisce sempre una riga nelle condizioni normali.

## 7. Annulla le prenotazioni non utilizzabili

Aggiungi un secondo **JDBC Query** chiamato `AnnullaPrenotazione` con la stessa connessione:

```sql
SELECT public.annulla_prenotazione(CAST(? AS UUID), ?) AS esito
```

Prepared Statement: `p_id` VARCHAR e `p_motivo` VARCHAR. Per `p_id` usa l'UUID ottenuto dal nome file; per `p_motivo` usa una costante, per esempio `'Richiesta rifiutata da TIBCO'`. Collega il Log `PrelievoRifiutato → AnnullaPrenotazione → SpostaRifiutato` con transizioni **Success**. Se `AnnullaPrenotazione` dà **Error**, registra l'errore e **lascia il file in input**: non liberare fondi soltanto spostando un file.

Dal **ParseXml** crea anche un ramo **Error** a un Log `XmlNonValido`, poi a una copia dell'attività `AnnullaPrenotazione` (es. `AnnullaXmlNonValido`), quindi a `SpostaXmlNonValido`. La funzione risponde `NON_TROVATA` per XML manuali senza prenotazione e li puoi comunque spostare. Se l'annullamento fallisce, lascia il file in input per riprovare/controllare.

## 8. Sposta i file con Rename File

Nella Palette **File** trascina un **Rename File** per ciascun ramo: `SpostaProcessed`, `SpostaRifiutato`, `SpostaXmlNonValido`, `SpostaNomeNonValido`.

Per tutti:

- `From Filename`: trascina `FilePoller → fileInfo → fullName` (percorso assoluto).
- `To Filename` di `SpostaProcessed`:

  ```xpath
  concat('C:/Users/utente/Desktop/Progetto ATM/processed/', $FilePoller/fileInfo/fileName)
  ```

- `To Filename` degli altri:

  ```xpath
  concat('C:/Users/utente/Desktop/Progetto ATM/error/', $FilePoller/fileInfo/fileName)
  ```

- Nel processo completo generato, **Overwrite** è attivo solo per `SpostaProcessed`: un retry con lo stesso UUID può sostituire l'XML già archiviato dopo che il database ha confermato `GIA_ELABORATA`, senza un altro addebito. Negli spostamenti verso `error` resta disattivo. Le cartelle devono esistere. Se lo spostamento fallisce, non dichiarare che il file è stato archiviato.

Il database può avere `ESEGUITA` mentre il file è ancora in `input` se Rename File fallisce. Al retry la funzione restituisce `GIA_ELABORATA` e il saldo non viene scalato ancora.

## 9. Salva, avvia e prova

1. Premi **Ctrl+S**, apri **Problems** e risolvi gli errori del modulo. Una freccia rimasta senza condizione o un mapping obbligatorio vuoto impedisce l'avvio.
2. Seleziona `ProgettoATM.application` → **Debug As → BW Application**. Aspetta l'avvio nella Console.
3. Nel terminale PowerShell della cartella principale, prepara il servizio web come indicato nel [README](../README.md), poi apri `http://127.0.0.1:3000`.
4. Usa Mario Rossi, PIN `12345`, 50 €. Dopo il clic, verifica un file `UUID.xml` in `input`. Il popup significa che l'XML è stato salvato; poi TIBCO lo sposta in `processed` e aggiorna PostgreSQL.
5. In pgAdmin:

   ```sql
   SELECT nome, cognome, saldo_centesimi FROM public.clienti WHERE pin = '12345';
   SELECT id_richiesta, importo_centesimi, stato, messaggio
   FROM public.transazioni ORDER BY creata_il DESC LIMIT 10;
   ```

   Con saldo iniziale 50000, un solo prelievo da 50 € lascia 45000. Non ripetere lo script di creazione aspettandoti che ripristini il saldo: è volutamente non distruttivo.
6. Prova 80 € con **Altro importo**. Prova un PIN sbagliato da cinque cifre: la pagina deve rifiutarlo senza creare XML. Prova 600 €: con saldo iniziale 500 €, la pagina risponde `Saldo insufficiente` senza XML.
7. Per testare il retry, copia un XML già processato con **lo stesso UUID** in `input`: TIBCO deve ricevere `GIA_ELABORATA`, senza un secondo addebito, e sostituire l'archivio omonimo in `processed`. Controlla che il file sparisca da `input` e che il saldo rimanga invariato.

## 10. Se non funziona

| Sintomo | Controllo |
|---|---|
| Nessun file letto | Il Filename termina in `input\*.xml`? BW è avviato? Il file termina davvero in `.xml`? |
| ParseXml fallisce | Verifica `xmlString`, **Validate Output**, elemento globale e struttura del file. |
| `No of ? ...` | Il numero dei `?` deve essere identico alle righe Prepared Statement. |
| `NON_PRENOTATA` | Hai copiato un XML a mano senza passare dal servizio web? Serve prima la prenotazione nel DB. |
| `CONFLITTO_ID` | Nome del file e dati XML non corrispondono alla prenotazione originale. |
| Error JDBC | Controlla connessione, firma delle funzioni, permessi SQL e Console. Non spostare in `error` automaticamente. |
| File in input, DB `ESEGUITA` | Rename File fallito; correggi percorso/permessi e riprova lo stesso ID. |
| Pagina salva ma TIBCO non elabora | I due programmi devono vedere **la stessa cartella**. Su macchine diverse usa una cartella condivisa raggiungibile da entrambi e configura i permessi. |

Riferimenti: [TIBCO BW 6.8.0 Binding & Palette Reference](https://docs.tibco.com/pub/activematrix_businessworks/6.8.0/doc/pdf/TIB_BW_6.8.0_bindings_palletes_reference.pdf?id=5), [transizioni BW](https://docs.tibco.com/pub/activematrix_businessworks/6.11.0/doc/html/app-dev-guide/working-with-transit.htm), [lock PostgreSQL](https://www.postgresql.org/docs/current/explicit-locking.html). Le schermate possono avere piccole differenze fra BW 6.8 e la documentazione 6.11 delle transizioni.
