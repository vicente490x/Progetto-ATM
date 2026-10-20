# Guida pratica ATM — TIBCO BusinessWorks 6

> Questa era la guida dell'esercizio iniziale con saldo di prova. Per il flusso completo con PostgreSQL, prenotazione e pagina web usa [TIBCO_BW6_SETUP.md](TIBCO_BW6_SETUP.md).

Questa guida serve per lavorare in Business Studio anche senza molta esperienza. Segui le fasi nell'ordine indicato. I passaggi già presenti vanno controllati, non ricreati.

## 0. Da dove parti

Nel progetto salvato, controllato il 20 ottobre 2026, sono presenti:

- il modulo `ProgettoATM` e l'applicazione `ProgettoATM.application`;
- lo schema [TransazioneATM.xsd](../ProgettoATM/Schemas/TransazioneATM.xsd) nel modulo;
- il processo [Process.bwp](../ProgettoATM/Processes/progettoatm/Process.bwp);
- `FilePoller → ParseXml`;
- il collegamento `$FilePoller/fileContent/textContent` all'input di ParseXml;
- la validazione dello schema attiva.

Questo controllo dei file non è un collaudo del processo in esecuzione.

Il manifest riporta BW 6.8.0. I riferimenti online riportati in fondo comprendono altre versioni BW 6: se un'etichetta differisce, usa la scheda **Reference - online** dell'attività nella tua installazione per verificarla.

Prima costruirai un esercizio che legge, verifica e archivia una richiesta confrontandola con 500 €. Questo esercizio **non aggiorna un conto**. Le fasi finali spiegano come sostituirlo con saldo e registro persistenti: sono necessarie per completare i requisiti originari.

## 1. Orientarti nella schermata

1. A sinistra, **Project Explorer** contiene i progetti e i file.
2. Apri `ProgettoATM → Processes → progettoatm → Process.bwp`.
3. Al centro c'è il diagramma.
4. La **Palette** contiene le attività da trascinare nel diagramma.
5. Selezionando un'attività, il pannello **Properties** mostra la sua configurazione.
6. Selezionando una freccia, Properties mostra la configurazione della **transizione**.
7. **Problems** elenca gli errori del progetto; **Console** mostra i messaggi di esecuzione.

Una transizione è una freccia che stabilisce quale attività eseguire dopo. Il mapping è il collegamento fra un dato già disponibile e il campo di input di un'altra attività.

Salva con **Ctrl+S** dopo ogni fase. Non modificare a mano il file `.bwp` mentre lo stai progettando nell'editor grafico.

## 2. Controllare le cartelle

Apri in Esplora file la cartella del progetto. Sono già presenti:

- [input](../input): richieste da leggere;
- [processed](../processed): richieste riuscite;
- [error](../error): richieste non valide o rifiutate.

Useremo queste cartelle, non `C:\ATM` indicato come esempio nella prima guida.

Non inserire file di prova finché non hai preparato anche i rami di successo ed errore. Conserva gli originali in [examples](../examples) e usa delle copie.

## 3. Verificare il File Poller

Seleziona **FilePoller → Properties → General**:

| Campo | Valore |
|---|---|
| Filename | `C:\Users\utente\Desktop\Progetto ATM\input\*.xml` |
| Polling Interval (sec) | `5` |
| Include Existing Files | Selezionato |
| Include Timestamp | Deselezionato |
| Exclude File Content | **Deselezionato** |
| Content as | `Text` |
| Encoding | `UTF-8` |

Attenzione al nome effettivo della casella: nella tua versione è **Exclude File Content**. Deve restare vuota per leggere il contenuto. La precedente indicazione di selezionare “Read Content” si riferiva all'opzione inversa.

In **Advanced**:

| Campo | Valore |
|---|---|
| Poll for Create Events | Selezionato |
| Poll for Modify Events | Deselezionato |
| Poll for Delete Events | Deselezionato |
| Include Sub-Directories | Deselezionato |
| Mode | Puoi mantenere `Files and Directories` con il filtro `*.xml` e la cartella riservata ai file |
| Sequence Key / Custom Job Id | Vuoti in questa prima prova |

Le opzioni di ordinamento possono restare come sono: non garantiscono la serializzazione degli addebiti.

**Verifica:** Filename deve terminare con `input\*.xml`, non con `.xsd`.

## 4. Verificare Parse XML

L'attività esiste già con il nome **ParseXml**.

1. Selezionala nel diagramma.
2. In **General**, controlla `Input Style = Text`.
3. Seleziona **Validate Output**.
4. In **Output Editor**, controlla che sia selezionato l'elemento globale `TransazioneATM` dello schema nel modulo. Non selezionare solo `Cliente`.
5. In **Input**, a sinistra espandi `FilePoller → fileContent`.
6. Il campo `textContent` deve essere collegato al campo `xmlString` sulla destra.

L'espressione salvata nel tuo processo è:

```xpath
$FilePoller/fileContent/textContent
```

Non incollare il percorso del file XSD dentro `xmlString`: questo campo riceve il testo della richiesta.

Se una freccia manca, usa lo strumento **Transition** del diagramma: seleziona l'attività di partenza, poi quella di arrivo. Per `FilePoller → ParseXml` scegli **Success**.

**Verifica:** l'output di ParseXml deve esporre `Cliente` e `DettagliPrelievo`. Non serve aggiungere Read File: il File Poller legge già il contenuto.

## 5. Aggiungere le attività che mostreranno gli esiti

Nella Palette cerca **Log**, nella categoria **General Activities**. Trascina quattro attività nel diagramma.

Rinominale in **Properties → General → Name**:

| Nome dell'attività | Messaggio |
|---|---|
| `ClienteOK` | `Cliente riconosciuto` |
| `ClienteKO` | `Cliente o PIN non riconosciuti` |
| `SaldoKO` | `Saldo insufficiente` |
| `XmlKO` | `XML non valido rispetto allo schema` |

Per ogni attività apri **Input**, seleziona il campo `message` e inserisci il testo come stringa XPath. Esempio:

```xpath
'Saldo insufficiente'
```

Se sono richiesti livello o logger, scegli `INFO` per ClienteOK e `WARN` per gli esiti negativi, usando il nome `atm.demo` come logger se il campo è disponibile. Non cambiare la configurazione globale dei log.

Non collegare l'intero XML al messaggio: conterrebbe il PIN.

## 6. Controllare il cliente con le transizioni

Per questo esercizio iniziale useremo soltanto Mario Rossi, PIN `12345`.

Non occorre cercare un'attività chiamata “If”: puoi fare la scelta con due transizioni.

### 6.1 Ramo del cliente riconosciuto

1. Crea una transizione da **ParseXml** a **ClienteOK**.
2. Seleziona la freccia.
3. In **Properties**, cerca **Condition Type**.
4. Scegli **Success with condition**.
5. Apri l'editor della condizione XPath.
6. Inserisci:

```xpath
normalize-space($ParseXml/Cliente/Nome) = 'Mario'
and normalize-space($ParseXml/Cliente/Cognome) = 'Rossi'
and string($ParseXml/Cliente/PIN) = '12345'
```

Questi percorsi corrispondono al nome `ParseXml` e all'elemento di output salvati nel progetto. Se rinomini l'attività o Business Studio genera percorsi diversi, trascina i campi dall'albero dei dati nell'editor e usa i percorsi generati. Non aggiungere automaticamente un secondo livello `/TransazioneATM`.

### 6.2 Ramo del cliente sconosciuto

1. Crea una seconda transizione da **ParseXml** a **ClienteKO**.
2. Seleziona la freccia.
3. Scegli **Success with no matching condition**.

Questo ramo viene preso quando ParseXml è riuscito, ma il cliente non corrisponde.

### 6.3 Ramo XML non valido

1. Crea una terza transizione da **ParseXml** a **XmlKO**.
2. Seleziona la freccia.
3. Imposta **Condition Type = Error**.

In caso di errore del parser, usa i dati del FilePoller per identificare il file: l'output di ParseXml potrebbe non esistere.

**Verifica:** da ParseXml devono partire tre frecce con tre condizioni diverse. Non lasciarle tutte su Success.

## 7. Preparare lo spostamento del file riuscito

1. Cerca **Rename File** nella palette **File**.
2. Trascinalo nel diagramma e rinominalo `SpostaProcessed`.
3. Apri **Input**.
4. Nel campo `fromFileName` trascina dal FilePoller il campo che contiene il percorso completo del file letto, normalmente `fileInfo/fullName`.
5. Nel campo `toFileName` inserisci il percorso completo di destinazione, mantenendo il nome originale.

Se l'albero conferma `$FilePoller/fileInfo/fullName`, puoi usare:

```xpath
concat(
  'C:/Users/utente/Desktop/Progetto ATM/processed/',
  tokenize(
    translate(string($FilePoller/fileInfo/fullName), '\', '/'),
    '/'
  )[last()]
)
```

Questa espressione converte i separatori del percorso in `/`, prende l'ultimo componente, cioè il nome, e lo aggiunge alla cartella processed. Nell'editor XPath il carattere `\` qui è letterale.

Usa l'editor XPath 2.0 per questa espressione. Se è impostato su XPath 1.0, non incollarla: usa il campo che contiene solo il nome del file, se presente nell'output, e concatenalo al percorso di destinazione.

**Verifica:** `toFileName` deve contenere anche il nome, per esempio `.../processed/prova-001.xml`, non soltanto la cartella.

Non abilitare la sovrascrittura di un file esistente. Un nome già presente deve essere verificato, non cancellato per nascondere il problema.

## 8. Controllare un saldo di prova

In questa fase il saldo è una costante di **500 € = 50000 centesimi**. Serve per capire i rami del processo; non dimostra un addebito né impedisce più prelievi consecutivi.

1. Crea una freccia da **ClienteOK** a **SpostaProcessed**.
2. Imposta **Success with condition**.
3. Inserisci:

```xpath
$ParseXml/DettagliPrelievo/Importo > 0
and ($ParseXml/DettagliPrelievo/Importo * 100) <= 50000
```

L'importo è di tipo decimal grazie all'XSD. Con al massimo due decimali, il prodotto per 100 rappresenta i centesimi.

4. Crea una seconda freccia da **ClienteOK** a **SaldoKO**.
5. Imposta **Success with no matching condition**.

**Verifica:** 80 e 100 passano; 600 viene rifiutato. Non aggiungere il vincolo “multiplo di 50”.

## 9. Spostare i file rifiutati

Per evitare problemi di confluenza dei rami mentre impari, usa tre attività Rename File distinte:

- `SpostaErroreCliente`, dopo ClienteKO;
- `SpostaErroreSaldo`, dopo SaldoKO;
- `SpostaErroreXml`, dopo XmlKO.

Per ciascuna:

1. Trascina Rename File dalla Palette e assegna il nome.
2. Collega il Log corrispondente con una transizione **Success**.
3. Mappa `fromFileName` dal percorso completo del FilePoller.
4. Mappa `toFileName` con la stessa espressione della fase 7, sostituendo `/processed/` con `/error/`.

Si tratta di uno **spostamento**, non di una copia: a operazione riuscita il file non deve restare in input.

Per ogni Rename File aggiungi inoltre un Log separato sul ramo **Error**, con un messaggio del tipo:

```xpath
'Archiviazione non riuscita: verificare percorso, permessi e file già presente'
```

Se lo spostamento fallisce, non dichiarare archiviata la richiesta. Il file può rimanere in input e richiedere un retry; con i soli eventi di creazione, il poller non garantisce un nuovo tentativo finché il file rimane invariato.

## 10. Controllare il diagramma

```text
FilePoller
    |
ParseXml
    +-- Error ------------------------> XmlKO ------> SpostaErroreXml
    |
    +-- Cliente riconosciuto ---------> ClienteOK
    |                                      |
    |                                      +-- Importo entro 500 € --> SpostaProcessed
    |                                      |
    |                                      +-- Altrimenti ----------> SaldoKO --> SpostaErroreSaldo
    |
    +-- Nessuna condizione soddisfatta -> ClienteKO --> SpostaErroreCliente
```

In questa fase “processed” significa che la richiesta ha superato i controlli dell'esercizio. Nella versione finale lo spostamento dovrà avvenire dopo la conferma dell'addebito persistente.

1. Salva tutto.
2. Apri **Problems**.
3. Filtra mentalmente gli errori relativi al tuo modulo: non limitarti al colore dell'icona.
4. Doppio clic su ogni errore per aprire l'attività interessata.
5. Risolvi input obbligatori mancanti, schema non selezionato e XPath non validi.

Un messaggio non visibile in Console può dipendere dalla configurazione del logger: verifica anche l'attività e i suoi dati nel debugger.

## 11. Avviare il debug

1. Controlla che le cartelle di prova non contengano richieste rimaste da una prova precedente.
2. Seleziona **ProgettoATM.application** nel Project Explorer.
3. Clic destro → **Debug As → BW Application**, se disponibile.
4. Se il comando non compare, apri **Run → Debug Configurations**, seleziona la configurazione per le applicazioni BW e includi ProgettoATM.application.
5. Accetta l'apertura della prospettiva Debug, se viene proposta.
6. Aspetta il messaggio di avvio dell'applicazione nella Console. Se compare un errore di avvio, risolvilo prima di copiare file.
7. Inserisci una sola richiesta per volta.

Per evitare che il poller legga una copia ancora in corso:

1. Prepara una copia dell'esempio fuori da input.
2. Rinominala `prova-001.tmp`.
3. Copiala in input.
4. Solo dopo la fine della copia rinominala `prova-001.xml`.

In Esplora file attiva la visualizzazione delle estensioni, così il nome non diventa per errore `prova-001.xml.tmp`.

Attendi almeno un intervallo di polling e controlla Console e cartella di destinazione. Alla fine delle prove arresta la sessione con **Terminate** nella vista Debug.

## 12. Eseguire le prove iniziali

Usa un nome nuovo per ciascuna prova indipendente. Mantieni lo stesso nome solo quando vuoi verificare un duplicato nella versione persistente.

| Prova | Dati | Atteso nell'esercizio |
|---|---|---|
| XML valido | Copia di [prelievo_valido.xml](../examples/prelievo_valido.xml) | Riconoscimento cliente e spostamento in processed |
| PIN corto | Copia di [pin_non_valido.xml](../examples/pin_non_valido.xml) | Errore XSD e spostamento in error |
| PIN sbagliato ma di 5 cifre | Copia dell'esempio valido con PIN `54321` | ClienteKO e spostamento in error |
| Importo negativo | Copia di [importo_non_valido.xml](../examples/importo_non_valido.xml) | Errore XSD e spostamento in error |
| Saldo insufficiente | Copia di [saldo_insufficiente.xml](../examples/saldo_insufficiente.xml), importo 600 | XSD valido, SaldoKO, spostamento in error |
| Importo libero | Copia dell'esempio valido con importo `80` | Spostamento in processed |
| Nome mancante | Copia senza elemento Nome | Errore XSD e spostamento in error |
| Errore di archiviazione | Destinazione di prova non accessibile | Log di errore, nessuna falsa conferma |

Per il caso saldo 100 €, importo 200 €, usa temporaneamente `10000` centesimi nella condizione della fase 8. Registra il valore utilizzato e ripristinalo dopo la prova.

Nell'[Excel dei test](../Consegna_esame/Casi_di_test_ATM.xlsx) registra solo ciò che hai verificato. Queste prove TIBCO non dimostrano il popup, i radio button o la validazione nel browser: quei casi richiedono anche il frontend.

## 13. Passare al saldo persistente: parte necessaria per il progetto completo

Non lasciare 500 fisso nella versione finale. Una normale variabile di processo non è un archivio di saldi; il fatto che una variabile si chiami “shared” non dimostra che sopravviva ai riavvii.

Per questa parte serve sapere quale database e quale driver JDBC sono disponibili nel laboratorio. Non è possibile dare un URL JDBC o una procedura SQL eseguibile senza questa scelta. Non installare un database a caso solo per seguire la guida.

Le operazioni in Business Studio saranno:

1. Espandi **Resources** nel modulo.
2. Usa **New** per creare una shared resource di tipo **JDBC Connection**; se non è nel menu breve, cercala in **New → Other**.
3. Configura driver, URL, utente e password del database del laboratorio.
4. Esegui il test di connessione, se disponibile nella risorsa.
5. Prepara nel database un archivio clienti con saldo in centesimi e un registro delle transazioni con identificativo univoco.
6. Aggiungi al processo un'attività JDBC per chiamare l'operazione di prelievo; la scelta fra query e procedura dipende dal contratto SQL implementato.
7. Seleziona la connessione creata.
8. Mappa come parametri identificativo del file, Nome, Cognome, PIN e importo in centesimi. Non concatenare i valori dentro il testo SQL.
9. Sostituisci i controlli su Mario e sul saldo fisso con i rami basati sull'esito restituito dal database.
10. Mantieni Rename File **fuori e dopo** la transazione del database.

L'operazione SQL deve svolgere in una sola transazione:

1. Cercare l'identificativo della richiesta.
2. Se è già completata e i dati coincidono, restituire l'esito precedente senza addebitare.
3. Se lo stesso identificativo ha dati diversi, restituire un conflitto.
4. Riconoscere il cliente.
5. Controllare e aggiornare il saldo in modo atomico, evitando che due richieste concorrenti spendano gli stessi fondi.
6. Registrare l'esito con un vincolo univoco sull'identificativo.
7. Eseguire il commit.

Un semplice “SELECT saldo” seguito da “UPDATE saldo” senza protezione transazionale non basta.

Puoi realizzare l'atomicità in una procedura del database oppure con attività JDBC dentro un gruppo transazionale compatibile con la connessione. Non mescolare le due modalità senza definirne i confini.

Il contratto dell'esito può essere: `OK`, `GIA_ELABORATA`, `CLIENTE_NON_VALIDO`, `SALDO_INSUFFICIENTE`, `CONFLITTO_ID`. Sono nomi proposti per il tuo progetto, non attività TIBCO predefinite.

## 14. Gestire duplicati, riavvii e problemi tecnici

1. Usa il nome univoco del file come identificativo, conservandolo nei retry.
2. Se il database conferma OK, sposta in processed.
3. Se conferma GIA_ELABORATA con gli stessi dati, completa l'archiviazione senza addebito.
4. Se rifiuta il cliente o il saldo, sposta in error e registra il motivo.
5. Se il database non risponde, non trattare l'errore come “saldo insufficiente”.
6. Se non sai se il commit è riuscito, interroga il registro con lo stesso identificativo prima di riprovare.
7. Se il commit è riuscito ma Rename File fallisce, il retry deve completare soltanto lo spostamento.
8. Nel processo completo, la ripetizione dello stesso ID già `ESEGUITA` può sostituire solo l'XML omonimo in `processed`, dopo il controllo del database. Gli spostamenti verso `error` non sovrascrivono file.
9. Mantieni Include Existing Files attivo per recuperare richieste rimaste in input al riavvio.

Prove da aggiungere: stesso file due volte, riavvio, due richieste da 80 € con disponibilità 100 €, errore dopo il commit e prima dello spostamento. Il risultato dell'ultima prova deve essere un solo addebito.

## 15. Collegare il servizio locale e la pagina

Quando il processo è verificato:

1. Configura il servizio locale affinché scriva nella stessa cartella input del File Poller.
2. Fai scrivere prima `.tmp`, poi rinominare `.xml` nella stessa cartella.
3. Conserva l'identificativo della richiesta quando la pagina riprova un invio.
4. Il servizio deve conservare prenotazioni persistenti per impedire che le richieste ancora in attesa superino la disponibilità.
5. TIBCO gestisce l'addebito centrale una sola volta; non deve sottrarre nuovamente dal saldo locale già ridotto dalle prenotazioni.
6. Definisci come riconciliare gli esiti con le prenotazioni. In assenza di conferma certa, non liberare automaticamente i fondi.
7. Il browser mostra “Prelevare il denaro entro 30 secondi” soltanto dopo la conferma del salvataggio. Il popup non certifica l'addebito TIBCO.

Con due archivi, locale e centrale, serve una regola di riconciliazione. Per il laboratorio, documenta se è manuale; non presentare i due saldi come sincronizzati automaticamente.

## 16. Preparare la dimostrazione dell'esame

1. Parti da un saldo e da un registro di prova noti.
2. Mostra un XML valido e lo schema.
3. Spiega File Poller, mapping e Parse XML.
4. Esegui una richiesta valida.
5. Mostra il file in processed e, nella versione completa, l'addebito registrato.
6. Esegui un PIN corto, un PIN errato di cinque cifre e un saldo insufficiente: spiega perché i rifiuti avvengono in punti diversi.
7. Ripeti una richiesta già elaborata e mostra che il saldo non cambia.
8. Mostra il registro test compilato con le prove effettivamente svolte.

La parte base e la parte persistente vanno presentate per quello che sono: il confronto con un saldo fisso è un esercizio sui rami, non una gestione completa del prelievo.

## Problemi frequenti

| Problema | Controllo |
|---|---|
| Non parte nessun processo | Applicazione avviata, percorso corretto, estensione realmente `.xml`, eventi Create abilitati |
| ParseXml riceve un testo vuoto | Exclude File Content deve essere vuoto; controlla mapping di textContent |
| Non compaiono i campi in output | Selezionare l'elemento globale TransazioneATM in Output Editor |
| Tutti i rami partono | Le frecce sono rimaste su Success; impostare le condizioni |
| Rename File fallisce | Percorso completo di origine e destinazione, cartella esistente, permessi, collisioni di nomi |
| XML valido ma cliente rifiutato | Controllare spazi, maiuscole, PIN e percorsi XPath |
| Importo 600 supera l'XSD | È normale: il confronto col saldo è applicativo |
| Il saldo torna sempre a 500 | È ancora attivo l'esercizio a saldo fisso |
| Dopo un riavvio compare un doppio addebito | Registro e aggiornamento saldo non sono correttamente persistenti e atomici |

## Riferimenti ufficiali

- [TIBCO BW 6.11 — Parse XML](https://docs.tibco.com/pub/activematrix_businessworks/6.11.0/doc/html/binding-palette/parse-xml.htm): input Text, Output Editor e Validate Output.
- [TIBCO BW 6.11 — Working with Transitions](https://docs.tibco.com/pub/activematrix_businessworks/6.11.0/doc/html/app-dev-guide/working-with-transit.htm): Success, condizioni, ramo senza corrispondenza ed Error.
- [TIBCO BW 6.7 — Activity Icons Reference](https://docs.tibco.com/pub/activematrix_businessworks/6.7.0/doc/html/GUID-25DF86E3-7A27-43AE-AA4B-7B1DA54F7EDC.html): attività disponibili, fra cui Log.
- [TIBCO BW 6.6 — File Palette](https://docs.tibco.com/pub/activematrix_businessworks/6.6.0/doc/html/GUID-CEC25132-84CC-4186-955F-00C975A3948D.html): Rename File per rinominare o spostare file.

Per i dettagli della versione 6.8 installata, usa anche la Reference dell'attività in Business Studio.
