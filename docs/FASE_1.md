# Fase 1 — formato della richiesta di prelievo

Questa pagina documenta la preparazione iniziale del formato XML. In quella fase non era ancora presente un processo TIBCO e non veniva eseguito alcun prelievo.

Per continuare lo sviluppo, segui la [guida completa TIBCO BW 6.8 con PostgreSQL e pagina web](TIBCO_BW6_SETUP.md). Il processo contiene già FilePoller, ParseXml, LeggiClienti e alcuni Log: controllali e completa il percorso. La guida usa le cartelle input, processed ed error presenti nella cartella del progetto; i percorsi `C:\ATM` sotto sono gli esempi della fase iniziale.

## File creati

Per preparare il database scelto per il progetto, prosegui con
[Fase 2 — PostgreSQL](FASE_2_POSTGRESQL.md).

| File | Scopo |
| --- | --- |
| `../schemas/TransazioneATM.xsd` | Definisce struttura, ordine e tipi dei dati del prelievo, senza namespace. |
| `../examples/prelievo_valido.xml` | Richiesta di esempio: Mario Rossi, PIN `12345`, importo `100`. |
| `../examples/pin_non_valido.xml` | PIN `123`: esempio da rifiutare perché non ha cinque cifre. |
| `../examples/importo_non_valido.xml` | Importo `-50`: esempio da rifiutare perché non è positivo. |
| `../examples/saldo_insufficiente.xml` | Importo `600`: XML corretto da confrontare in seguito con un saldo di prova di `500` euro. |
| `FASE_1.md` | Questa guida. |

Lo schema richiede Nome e Cognome non vuoti, un PIN testuale di esattamente cinque cifre ASCII (`0`–`9`), un Importo positivo con al massimo due cifre dopo il punto e una DataOra di tipo `xs:dateTime`. Il PIN resta una stringa: per esempio `01234` conserva lo zero iniziale. Per l'importo XML si usa il punto come separatore decimale. `xs:dateTime` accetta sia l'orario dell'esempio, senza indicazione di fuso, sia un orario con fuso come quello del TAD.

## Verifica eseguita

I quattro file sono stati letti e confrontati con lo schema tramite `System.Xml.XmlReader` e `System.Xml.Schema.XmlSchemaSet` di .NET su Windows.

| Esempio | Esito atteso | Esito ottenuto | Motivo |
| --- | --- | --- | --- |
| `prelievo_valido.xml` | Valido | Valido | Formato corretto. |
| `pin_non_valido.xml` | Non valido | Non valido | Il PIN contiene tre cifre. |
| `importo_non_valido.xml` | Non valido | Non valido | L'importo è negativo. |
| `saldo_insufficiente.xml` | Valido | Valido | `600` è un importo XML corretto. |

La validazione XSD controlla **il formato del file**. Non conosce i clienti e non conosce il saldo. Perciò `saldo_insufficiente.xml` supera la validazione: il confronto tra `600` euro richiesti e `500` euro disponibili sarà un **controllo del processo TIBCO** in una fase successiva.

## Cartelle runtime da preparare su Windows

Quando il processo TIBCO sarà pronto, prepara queste cartelle sul computer dove verrà eseguito:

- `C:\ATM\input` — richieste XML in attesa di lettura.
- `C:\ATM\processed` — richieste elaborate con successo.
- `C:\ATM\error` — richieste non valide o rifiutate.

Queste cartelle runtime non vengono usate in questa fase. Gli esempi rimangono nella cartella `examples`: non copiarli ancora in `C:\ATM\input`.

## Prossimo obiettivo

Aprire `../schemas/TransazioneATM.xsd` e `../examples/prelievo_valido.xml` per vedere il formato. Nella fase successiva realizzerai in TIBCO Business Studio un primo processo BW 6 che legge un file XML. A quel punto useremo la cartella `input` per la prova.
