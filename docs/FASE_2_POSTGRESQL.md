# Fase 2 — Preparare PostgreSQL

## Obiettivo

Creare nel database `atm_didattico` le tabelle `public.clienti` e
`public.transazioni`, con due clienti fittizi.
TIBCO si collegherà in seguito a questo stesso database tramite JDBC.

## Passaggi in pgAdmin

1. Espandi il server e il nodo **Databases**.
2. Seleziona **atm_didattico**.
3. Apri **Tools → Query Tool**.
4. Apri [01_creazione_tabelle.sql](../database/01_creazione_tabelle.sql)
   e copia tutto il contenuto nel Query Tool.
5. Esegui l'intero script, senza lasciare selezionata solo una parte.
6. Controlla la scheda **Messages**: non devono esserci errori.
7. In **Data Output** devono apparire Mario Rossi e Èlia D’Amico-Rossi.
   Alla prima esecuzione entrambi hanno 50000 centesimi, cioè 500,00 €.
8. Nell'albero a sinistra espandi
   **atm_didattico → Schemas → public → Tables**.
   Clic destro su **Tables → Refresh** se non vedi le tabelle.

Lo script non è stato eseguito sul tuo server da questa chat.
Il risultato nel Query Tool sarà la verifica effettiva.

## Cosa significano le due tabelle

| Tabella | Contenuto |
|---|---|
| clienti | Nome, cognome, PIN di prova e saldo contabile in centesimi |
| transazioni | Identificativo della richiesta, cliente, importo, stato e date |

Il PIN è testuale: `01234` non perde lo zero. È presente in chiaro solo
per i clienti fittizi della demo; non usarlo come modello per un sistema reale.

L'identificativo della transazione è un UUID e sarà anche la base del nome
del file XML. Una chiave primaria impedisce due righe con lo stesso ID,
ma **non basta da sola a impedire due addebiti**: servirà la funzione
transazionale che realizzeremo in un passaggio successivo.

Gli stati previsti sono:

- **PRENOTATA**: richiesta accettata, fondi impegnati, addebito non ancora eseguito;
- **ESEGUITA**: TIBCO ha confermato l'addebito;
- **RIFIUTATA**: richiesta conclusa senza addebito.

La disponibilità sarà il saldo contabile meno la somma delle prenotazioni
attive. Saldo, prenotazioni e registro resteranno tutti in PostgreSQL:
il servizio locale non avrà un secondo archivio di saldi.

Il passaggio PRENOTATA → ESEGUITA dovrà scalare il saldo e aggiornare
lo stato nella stessa transazione. Un retry di una richiesta ESEGUITA
non dovrà scalare nulla. Queste operazioni non sono ancora implementate
dal solo script di creazione.

## Verifica aggiuntiva

Esegui separatamente:

```sql
SELECT COUNT(*) AS numero_transazioni
FROM public.transazioni;
```

In un database appena preparato il risultato è `0`: non hai ancora
eseguito alcun prelievo.

## Se ripeti lo script

Le tabelle esistenti non vengono eliminate. `ON CONFLICT (pin) DO NOTHING`
evita di reinserire un PIN già presente e non ripristina il saldo a 500 €.
Se esistono già tabelle omonime con una struttura diversa, lo script non
le aggiorna: conserva l'errore e verifica la struttura prima di proseguire.

Se un errore lascia la sessione in stato di transazione fallita, esegui:

```sql
ROLLBACK;
```

Poi correggi la causa prima di ripetere lo script completo.

## Passaggio successivo

La JDBC Connection è stata configurata nel progetto di prova. Prosegui con
[la guida TIBCO completa](TIBCO_BW6_SETUP.md): esegui le funzioni SQL della
fase successiva, poi collega il prelievo atomico al processo BW. La password
si inserisce nella configurazione locale: non va copiata nella chat o nei
file da consegnare.

Riferimenti ufficiali:
[colonne identity](https://www.postgresql.org/docs/current/ddl-identity-columns.html)
e [INSERT / ON CONFLICT](https://www.postgresql.org/docs/current/sql-insert.html).
