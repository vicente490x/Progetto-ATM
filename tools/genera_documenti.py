"""Prepara i documenti per l'esame e il registro Excel, senza dipendenze esterne."""
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Consegna_esame'
OUT.mkdir(exist_ok=True)
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
S = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
P = 'http://schemas.openxmlformats.org/package/2006/relationships'
XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'


def para(text, style='Normal'):
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'


def link(label, rid):
    return f'<w:p><w:hyperlink r:id="{rid}"><w:r><w:rPr><w:rStyle w:val="Hyperlink"/></w:rPr><w:t>{escape(label)}</w:t></w:r></w:hyperlink></w:p>'


def page_break():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def make_docx(filename, paragraphs, links=()):
    styles = f'''{XML}<w:styles xmlns:w="{W}">
      <w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/><w:lang w:val="it-IT"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/><w:widowControl/></w:pPr></w:pPrDefault></w:docDefaults>
      <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
      <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="0" w:after="140"/></w:pPr><w:rPr><w:b/><w:color w:val="203A53"/><w:sz w:val="34"/></w:rPr></w:style>
      <w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:after="240"/></w:pPr><w:rPr><w:color w:val="555555"/><w:sz w:val="22"/></w:rPr></w:style>
      <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="220" w:after="100"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:color w:val="203A53"/><w:sz w:val="26"/></w:rPr></w:style>
      <w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Codice XML"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:after="0" w:line="220" w:lineRule="auto"/><w:shd w:fill="F3F5F7"/></w:pPr><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="19"/></w:rPr></w:style>
      <w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr></w:style>
    </w:styles>'''
    body = ''.join(paragraphs)
    section = '<w:sectPr><w:footerReference w:type="default" r:id="rIdFooter"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="567" w:footer="567"/></w:sectPr>'
    document = f'{XML}<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>{body}{section}</w:body></w:document>'
    rels = [f'<Relationship Id="rIdStyles" Type="{R}/styles" Target="styles.xml"/>', f'<Relationship Id="rIdFooter" Type="{R}/footer" Target="footer1.xml"/>']
    for rid, target in links:
        rels.append(f'<Relationship Id="{rid}" Type="{R}/hyperlink" Target="{escape(target, {chr(34): "&quot;"})}" TargetMode="External"/>')
    footer = f'{XML}<w:ftr xmlns:w="{W}"><w:p><w:pPr><w:jc w:val="right"/></w:pPr><w:r><w:rPr><w:color w:val="666666"/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve">Progetto ATM · </w:t></w:r><w:fldSimple w:instr="PAGE"><w:r><w:t>1</w:t></w:r></w:fldSimple></w:p></w:ftr>'
    types = f'''{XML}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/></Types>'''
    with ZipFile(OUT / filename, 'w', ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', types)
        z.writestr('_rels/.rels', f'{XML}<Relationships xmlns="{P}"><Relationship Id="rId1" Type="{R}/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr('word/document.xml', document)
        z.writestr('word/styles.xml', styles)
        z.writestr('word/footer1.xml', footer)
        z.writestr('word/_rels/document.xml.rels', f'{XML}<Relationships xmlns="{P}">{"".join(rels)}</Relationships>')


doc = [
    para('Progetto ATM Bancomat', 'Title'),
    para('BUR e FUD – progetto per l’esame di TIBCO BW 6', 'Subtitle'),
    para('In questi documenti descrivo come intendo realizzare il progetto partendo dalla traccia. Le prove sono raccolte nel file Excel allegato. I risultati andranno compilati durante il collaudo.'),
    para('1. BUR – Richieste del cliente', 'Heading1'),
    para('Il cliente richiede un’applicazione per un ATM che permetta soltanto di prelevare denaro. Non sono previste altre operazioni, come versamenti, bonifici o ricariche.'),
    para('Per essere riconosciuto, l’utente deve inserire nome, cognome e un PIN di cinque cifre. I dati devono corrispondere a un cliente presente nel sistema: non basta inserire un PIN della lunghezza giusta.'),
    para('L’utente deve poter scegliere un importo di 50 €, 100 € o 200 € tramite radio button. Deve essere disponibile anche un campo per un importo libero. La richiesta può essere accettata soltanto se il saldo disponibile è sufficiente.'),
    para('I dati del prelievo devono essere salvati in un file XML nella cartella che sarà letta da TIBCO BW 6. Dopo il salvataggio deve comparire il popup “Prelevare il denaro entro 30 secondi”. In caso di errore, l’applicazione deve spiegare il problema e non mostrare il popup di successo.'),
    para('2. FUD – Come ho interpretato la richiesta', 'Heading1'),
    para('La pagina conterrà i campi Nome, Cognome e PIN. Il PIN sarà un campo password. Sotto i dati del cliente inserirò i tre importi standard e l’opzione “Altro importo”, con il relativo campo. Sarà possibile utilizzare una sola scelta alla volta e l’importo da inviare sarà sempre visibile.'),
    para('Premendo “Conferma Prelievo”, la pagina controllerà i campi obbligatori, le cinque cifre del PIN e l’importo. Nome e cognome potranno contenere accenti, spazi, apostrofi e trattini. Per l’importo saranno ammessi punto o virgola e al massimo due decimali; zero, numeri negativi e testo non saranno accettati. Anche 80 € dovrà essere accettato, se il saldo lo permette.'),
    para('Il servizio locale ripeterà i controlli, riconoscerà il cliente e verificherà il saldo. Se tutto è corretto, prenoterà l’importo e salverà il file XML. La prenotazione serve a evitare che più richieste ancora in attesa superino insieme il saldo disponibile.'),
    page_break(),
    para('2.1 Esito della richiesta e messaggi', 'Heading1'),
    para('Il pulsante sarà disabilitato durante l’invio. Ogni richiesta avrà un identificativo: se si interrompe la connessione, il tentativo successivo userà lo stesso identificativo, così non verranno creati un secondo file o una seconda prenotazione.'),
    para('Se il PIN non contiene esattamente cinque cifre, comparirà “Il PIN deve essere di 5 cifre”. Se i dati non corrispondono a un cliente, comparirà “Cliente o PIN non riconosciuti”. Se l’importo supera il saldo disponibile, comparirà “Saldo insufficiente”.'),
    para('Il popup “Prelevare il denaro entro 30 secondi” comparirà soltanto quando il servizio confermerà il salvataggio. Nel progetto questo messaggio è richiesto dalla traccia: non dimostra che TIBCO abbia già elaborato il prelievo. L’esito del processo TIBCO sarà verificato separatamente.'),
    para('2.2 Dati usati per la dimostrazione', 'Heading1'),
    para('Userò soltanto clienti fittizi. Il cliente principale sarà Mario Rossi, con PIN 12345 e saldo iniziale di 500 € nelle prove positive. Per il test sul saldo insufficiente partirò invece da 100 €. Ogni prova dovrà iniziare dai dati indicati nell’Excel, senza dipendere dalle prove precedenti.'),
    para('Aggiungerò anche Èlia D’Amico-Rossi, con PIN 01234 e saldo di 500 €, per controllare accenti, apostrofi, trattini e lo zero iniziale del PIN. Il saldo della dimostrazione sarà configurabile.'),
    para('3. Casi di test nel file Excel', 'Heading1'),
    para('La tabella completa è nel file Casi_di_test_ATM.xlsx, da tenere nella stessa cartella di questo documento. Ho riportato i cinque casi principali della traccia e aggiunto le prove sui controlli, sul salvataggio e sul processo TIBCO.'),
    link('Apri la tabella Excel: Casi_di_test_ATM.xlsx', 'rIdExcel'),
    para('Nel foglio “Casi di test” sono indicati i dati iniziali, i passaggi e il risultato atteso. Le colonne “Risultato ottenuto”, “Esito”, “Data prova” e “Note / evidenze” vanno compilate durante l’esecuzione. Per ora tutti i casi sono segnati come “Da eseguire”.'),
    para('Per considerare superato un caso controllerò sia ciò che compare nella pagina sia i file creati. Per le prove TIBCO controllerò anche il registro delle richieste elaborate e le cartelle processed ed error. I dettagli tecnici sono nel TAD allegato.'),
    link('Apri il TAD: TAD_Architettura_Tecnica_ATM.docx', 'rIdTAD'),
]
make_docx('Documenti_progetto_ATM.docx', doc, [('rIdExcel', 'Casi_di_test_ATM.xlsx'), ('rIdTAD', 'TAD_Architettura_Tecnica_ATM.docx')])

sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<TransazioneATM>
  <Cliente>
    <Nome>Mario</Nome>
    <Cognome>Rossi</Cognome>
    <PIN>12345</PIN>
  </Cliente>
  <DettagliPrelievo>
    <Importo>100.00</Importo>
    <DataOra>2026-10-19T11:00:00+02:00</DataOra>
  </DettagliPrelievo>
</TransazioneATM>'''
tad = [
    para('TAD – Architettura tecnica', 'Title'),
    para('Progetto ATM Bancomat con TIBCO BW 6', 'Subtitle'),
    para('1. Organizzazione del progetto', 'Heading1'),
    para('Ho previsto tre parti: una pagina HTML con CSS e JavaScript, un piccolo servizio locale in Node.js con Express e un processo TIBCO BW 6. La pagina raccoglierà la richiesta, il servizio salverà l’XML e TIBCO lo leggerà per elaborare il prelievo.'),
    para('Il flusso sarà: pagina → servizio locale → cartella input → TIBCO → cartella processed oppure error. Pagina e API saranno servite dallo stesso indirizzo locale. Il servizio ascolterà su 127.0.0.1.'),
    para('2. Controlli della richiesta', 'Heading1'),
    para('JavaScript controllerà i campi prima dell’invio. Il servizio ripeterà i controlli, perché quelli della pagina possono essere aggirati, e confronterà nome, cognome e PIN con l’archivio dei clienti fittizi.'),
    para('Per il PIN userò l’espressione ^[0-9]{5}$. Lo conserverò come stringa per non perdere lo zero iniziale. Nome e cognome saranno obbligatori dopo la rimozione degli spazi iniziali e finali. Gli importi saranno positivi, con al massimo due decimali; i confronti saranno fatti in centesimi interi.'),
    para('3. Esempio del file XML', 'Heading1'),
    para('Il file sarà scritto in UTF-8. L’importo avrà il punto decimale; data e ora saranno generate dal servizio al momento della richiesta, con il fuso orario. Questo è un esempio con dati di prova:'),
    *[para(line, 'Code') for line in sample_xml.splitlines()],
    para('I nomi degli elementi resteranno quelli della traccia. Lo schema XSD descriverà campi obbligatori, ordine degli elementi, PIN di cinque cifre, importo positivo e data con fuso. I caratteri riservati dell’XML saranno convertiti nelle rispettive entità, per esempio & in &amp;.'),
    page_break(),
    para('4. Salvataggio del file', 'Heading1'),
    para('Il browser non può scrivere liberamente in una cartella del computer. Per questo invierà i dati al servizio locale, che leggerà il percorso dalla variabile ATM_OUTPUT_DIR. Per la dimostrazione il percorso potrà essere C:\\ATM\\input.'),
    para('Il servizio genererà un identificativo univoco e lo userà come nome del file, per esempio <identificativo>.xml. Il client non potrà scegliere percorsi o nomi arbitrari. Lo stesso identificativo sarà mantenuto se si riprova una richiesta dopo un errore di rete.'),
    para('La scrittura avverrà prima in un file .tmp e poi, quando sarà completa, il file verrà rinominato .xml nella stessa cartella. TIBCO dovrà cercare soltanto i file .xml. Se il salvataggio fallisce, la pagina mostrerà un errore e non eseguirà il popup.'),
    para('Il PIN in chiaro nell’XML serve soltanto per rispettare il contratto della dimostrazione. Non userò dati reali e non scriverò il PIN nei log. Questo formato non è adatto a un ATM reale.'),
    para('5. Saldo e richieste ripetute', 'Heading1'),
    para('Per la demo ho previsto un archivio SQLite con clienti, saldo iniziale, prenotazioni e identificativi delle richieste. La disponibilità sarà il saldo iniziale meno gli importi già prenotati. Le prenotazioni resteranno salvate anche dopo il riavvio del servizio.'),
    para('Il controllo della disponibilità e la prenotazione dovranno avvenire nella stessa transazione del database. In questo modo, due richieste contemporanee non potranno impegnare più denaro di quello disponibile. Una richiesta ripetuta con lo stesso identificativo non creerà una seconda prenotazione; lo stesso identificativo con dati diversi sarà rifiutato.'),
    para('Il servizio locale gestirà solo la disponibilità della demo. TIBCO gestirà l’addebito nel proprio archivio centrale di prova, una sola volta per identificativo, senza sottrarre di nuovo denaro dal saldo locale. In questa prima versione non è previsto il riallineamento automatico dei due archivi: le prenotazioni resteranno occupate fino alla riconciliazione.'),
    para('Se la scrittura fallisce prima che il file sia pubblicato e l’esito è certo, la prenotazione dovrà essere annullata. Se il servizio si interrompe in un punto in cui non è chiaro se TIBCO abbia già ricevuto il file, conserverò la prenotazione e verificherò l’identificativo nel registro. Non creerò una nuova richiesta per risolvere l’incertezza.'),
    para('Prima di liberare fondi o azzerare una prova controllerò quindi che non ci siano file ancora in attesa. Durante il collaudo userò cartelle e dati separati per ogni scenario.'),
    page_break(),
    para('6. Processo da realizzare in TIBCO BW 6', 'Heading1'),
    para('1) File Poller: imposterò il percorso C:\\ATM\\input\\*.xml, un intervallo di controllo di 5 secondi e l’opzione Include Existing Files, così verranno considerate anche le richieste presenti prima dell’avvio. Gestirò gli eventi di creazione dei file.'),
    para('2) Lettura e analisi: userò Read File in UTF-8 per leggere il contenuto. Lo passerò a Parse XML, con Input Style impostato su Text. Nell’Output Editor selezionerò lo schema XSD di TransazioneATM e abiliterò Validate Output.'),
    para('3) Controlli: dopo la validazione dello schema, controllerò i dati del cliente, il PIN e l’importo. Lo schema verifica la struttura del messaggio, ma non può stabilire se il cliente esiste o se ha saldo sufficiente.'),
    para('4) Elaborazione: ricaverò l’identificativo dal nome del file e controllerò un registro persistente. Se la richiesta è già stata completata, non eseguirò un altro addebito. Per una richiesta nuova, registrazione dell’esito e aggiornamento del saldo centrale dovranno appartenere alla stessa transazione, con un vincolo di unicità sull’identificativo.'),
    para('5) Archiviazione: userò Rename File per spostare i file riusciti in processed. I file non validi o rifiutati saranno spostati in error. Registrerò identificativo e motivo dell’errore, senza riportare il PIN.'),
    para('6) Riavvii ed errori: se l’addebito è riuscito ma lo spostamento del file fallisce, al tentativo successivo il registro impedirà un secondo addebito. In caso di errore temporaneo riproverò lo stesso identificativo; per un errore di validazione correggerò prima la causa. Un esito incerto richiederà una verifica prima di proseguire.'),
    para('7. Cartelle condivise e verifica in laboratorio', 'Heading1'),
    para('Se servizio e TIBCO girano su computer diversi, userò una cartella condivisa raggiungibile da entrambi, per esempio \\\\server\\atm\\input. Verificherò i permessi degli utenti che eseguono i servizi e la rinomina del file sulla condivisione. Un percorso C:\\ATM\\input su due computer diversi non indica la stessa cartella.'),
    para('Le attività sono descritte con riferimento alla documentazione ufficiale BW 6.11. La versione e i nomi delle opzioni disponibili nel laboratorio andranno controllati in Business Studio. Questo TAD descrive un processo da realizzare: non riporta un collaudo TIBCO già eseguito.'),
    para('Riferimenti e prove', 'Heading1'),
    link('TIBCO BW 6.11 – File Poller', 'rIdPoller'),
    link('TIBCO BW 6.11 – Parse XML', 'rIdParse'),
    link('TIBCO BW 6.6 – File Palette (Rename File)', 'rIdFile'),
    link('Casi di test: apri Casi_di_test_ATM.xlsx', 'rIdExcel'),
]
make_docx('TAD_Architettura_Tecnica_ATM.docx', tad, [
    ('rIdPoller', 'https://docs.tibco.com/pub/activematrix_businessworks/6.11.0/doc/html/binding-palette/file-poller.htm'),
    ('rIdParse', 'https://docs.tibco.com/pub/activematrix_businessworks/6.11.0/doc/html/binding-palette/parse-xml.htm'),
    ('rIdFile', 'https://docs.tibco.com/pub/activematrix_businessworks/6.6.0/doc/html/GUID-CEC25132-84CC-4186-955F-00C975A3948D.html'),
    ('rIdExcel', 'Casi_di_test_ATM.xlsx'),
])

# ID, ambito, scenario, dati e condizioni iniziali, passi, risultato atteso.
cases = [
('TC_01','Pagina / servizio','Importo standard','Mario Rossi; PIN 12345; saldo disponibile 500 €; importo 50 €.','Compilare i dati; selezionare il radio 50 €; premere Conferma Prelievo.','Un solo XML con importo 50.00. Popup: “Prelevare il denaro entro 30 secondi”. Disponibilità demo residua 450 €.'),
('TC_02','Pagina / servizio','PIN troppo corto','Mario Rossi; PIN 123; saldo 500 €; importo 50 €.','Inviare prima dal modulo e poi direttamente all’API.','Messaggio “Il PIN deve essere di 5 cifre”. Nessun XML, nessuna prenotazione e nessun popup di successo.'),
('TC_03','Pagina / servizio','Importo libero di 80 €','Mario Rossi; PIN 12345; saldo 500 €; importo personalizzato 80 €.','Selezionare Altro importo; inserire 80; confermare.','Un XML con importo 80.00 e popup previsto. Disponibilità residua 420 €. Non è richiesto un multiplo di 50.'),
('TC_04','Pagina / servizio','Saldo insufficiente','Mario Rossi; PIN 12345; saldo disponibile 100 €; importo 200 €.','Selezionare 200 € e confermare.','Messaggio “Saldo insufficiente”. Nessun XML, nessuna prenotazione e nessun popup di successo.'),
('TC_05','File / XML','Nome univoco e conformità XSD','Cartella di test configurata; cliente valido; saldo 500 €; importo 100 €.','Inviare due richieste distinte; controllare i file e validarli con lo schema XSD.','Due nomi diversi con identificativo. XML UTF-8 valido: Cliente e DettagliPrelievo, dati corretti, importo con punto e DataOra con fuso.'),
('TC_06','Pagina / servizio','Campi anagrafici vuoti','Cliente di prova; PIN 12345; importo 50 €.','Provare nome vuoto, cognome vuoto e campi contenenti solo spazi; ripetere tramite API.','Richiesta rifiutata con messaggio sui campi obbligatori. Nessun XML e nessun popup.'),
('TC_07','Pagina / servizio','PIN non numerico o troppo lungo','Mario Rossi; importo 50 €; PIN 12a45 e 123456.','Provare il PIN con lettere nel modulo; inviare entrambe le varianti direttamente all’API.','Messaggio “Il PIN deve essere di 5 cifre”. Nessun XML, nessuna prenotazione.'),
('TC_08','Servizio','Credenziali non riconosciute','Mario Rossi con PIN 54321; poi nominativo assente con PIN 12345.','Inviare entrambe le richieste con un importo di 50 €.','Il formato del PIN è valido ma le credenziali vengono rifiutate. Nessun XML e nessun popup.'),
('TC_09','Pagina / XML','PIN con zero iniziale','Èlia D’Amico-Rossi; PIN 01234; saldo 500 €; importo 50 €.','Inviare la richiesta e leggere il PIN nell’XML.','Richiesta accettata; il PIN resta la stringa 01234, senza perdere lo zero iniziale.'),
('TC_10','Pagina / servizio','Importi non validi','Cliente valido; saldo 500 €; importi: vuoto, 0, -10, abc, NaN, Infinity, 1e2, 10.001.','Provare ogni valore come importo libero e tramite API.','Ogni valore viene rifiutato. Nessun XML, nessuna prenotazione e nessun popup di successo.'),
('TC_11','Pagina / XML','Importi con decimali','Cliente valido; saldo 500 € a ogni prova; importi 80,50 e 80.50.','Inviare separatamente i due formati; leggere importo e disponibilità.','Entrambi diventano 80.50 nell’XML e 8050 centesimi nei calcoli. Disponibilità residua 419,50 €.'),
('TC_12','Pagina / XML','Accenti, apostrofi e trattini','Èlia D’Amico-Rossi; PIN 01234; saldo 500 €. Altro cliente fittizio con apostrofo semplice e nome composto.','Registrare i nominativi nell’archivio di prova; inviarli con spazi iniziali e finali.','Spazi esterni rimossi; nominativi riconosciuti e conservati correttamente in UTF-8. Nessun XML malformato.'),
('TC_13','Servizio / XML','Escaping XML','Prova isolata del generatore XML; testo di prova contenente &, <, >, virgolette e apostrofo.','Passare il testo al generatore e rileggere l’XML con un parser.','Caratteri riservati codificati correttamente; il parser restituisce il testo originale. La prova non autorizza nominativi estranei all’archivio.'),
('TC_14','Salvataggio','Cartella non scrivibile','Cliente valido; saldo 500 €; utente del servizio privo del permesso di scrittura sulla cartella di prova.','Inviare una richiesta; verificare messaggio, file e prenotazione.','Errore comprensibile e nessun popup. Se non è stato pubblicato alcun XML e l’esito è certo, nessuna prenotazione resta attiva.'),
('TC_15','Saldo','Importo uguale alla disponibilità','Mario Rossi; PIN 12345; saldo disponibile 100 €; importo 100 €.','Inviare 100 €; poi provare una nuova richiesta da 0,01 €.','Prima richiesta accettata, disponibilità zero. Seconda richiesta rifiutata con “Saldo insufficiente”.'),
('TC_16','Idempotenza','Stessa richiesta inviata due volte','Cliente valido; saldo 500 €; importo 50 €; stesso identificativo e stessi dati.','Inviare due volte la richiesta, anche direttamente all’API.','Un solo XML, una sola prenotazione e disponibilità 450 €. Il secondo invio restituisce l’esito della stessa richiesta.'),
('TC_17','Idempotenza','Identificativo riusato con dati diversi','Prima richiesta: 50 €. Seconda: 100 €, con lo stesso identificativo.','Inviare la prima richiesta; poi ripetere l’identificativo cambiando l’importo.','Seconda richiesta rifiutata per conflitto. Nessun file sovrascritto e nessuna seconda prenotazione.'),
('TC_18','Saldo','Richieste concorrenti','Mario Rossi; saldo disponibile 100 €; due richieste da 80 € con identificativi diversi.','Inviare le due richieste contemporaneamente.','Una sola richiesta accettata e un solo XML. L’altra riceve “Saldo insufficiente”. Disponibilità residua 20 €.'),
('TC_19','Pagina / rete','Risposta persa dopo il salvataggio','Cliente valido; saldo 500 €; importo 50 €; possibilità di interrompere la risposta HTTP.','Far salvare la richiesta ma interrompere la risposta; poi riprovare dalla stessa scheda.','Nessun popup senza conferma. Il retry conserva l’identificativo: un solo XML e una sola prenotazione; popup solo dopo conferma.'),
('TC_20','Pagina','Scelta dell’importo e doppio click','Cliente valido; saldo 500 €; radio 100 € e campo libero 80 €.','Passare da Altro importo al radio 100 €; controllare il riepilogo; fare doppio click su Conferma.','Viene inviato solo 100 €. Il campo libero non prevale sul radio. Pulsante disabilitato durante l’invio e una sola richiesta.'),
('TC_21','Persistenza','Riavvio dopo una richiesta salvata','Saldo iniziale 100 €; richiesta da 80 € già salvata; identificativo noto.','Riavviare il servizio; ripetere la richiesta originale; poi inviarne una nuova da 50 €.','Prenotazione mantenuta, nessun duplicato al retry. La nuova richiesta da 50 € viene rifiutata: restano 20 € disponibili.'),
('TC_22','Persistenza','Interruzione durante la pubblicazione','Cliente valido; cartella e database isolati; possibilità di interrompere il servizio prima o dopo la rinomina.','Ripetere la prova interrompendo prima della rinomina e dopo la rinomina ma prima della conferma.','Il recupero usa lo stesso identificativo. Nessun secondo XML o doppia prenotazione. Se l’esito è incerto, fondi trattenuti e verifica richiesta, senza falso successo.'),
('TC_23','TIBCO','Elaborazione di un file valido','BW 6 configurato; XML valido; cliente nel sistema centrale; saldo centrale sufficiente; registro vuoto.','Avviare il processo e inserire un XML completo nella cartella input.','Parsing e controlli riusciti; un solo addebito centrale; identificativo registrato; file spostato in processed.'),
('TC_24','TIBCO','XML non conforme o richiesta rifiutata','Tre prove isolate: XML senza PIN; cliente sconosciuto; cliente valido con saldo centrale insufficiente.','Inserire ciascun file nella cartella input e osservare il ramo di errore.','Nessun addebito. File in error e motivo registrato senza PIN; per saldo insufficiente, motivo coerente con “Saldo insufficiente”.'),
('TC_25','TIBCO','File già elaborato letto di nuovo','Una transazione già completata e presente nel registro persistente.','Reinserire in input lo stesso file, mantenendo il nome; riavviare anche il processo.','Il registro riconosce l’identificativo e impedisce un secondo addebito. Il file viene gestito come già elaborato.'),
('TC_26','TIBCO','Errore dopo l’addebito','XML valido; possibilità di impedire lo spostamento in processed dopo il commit dell’addebito.','Elaborare il file; simulare il fallimento dello spostamento; ripristinare i permessi e riprovare.','Esito e addebito restano registrati. Il retry completa solo l’archiviazione; il saldo centrale non viene scalato di nuovo.'),
('TC_27','File / TIBCO','File temporanei e file presenti al riavvio','File Poller con filtro *.xml e Include Existing Files; .tmp incompleto in input.','Verificare che il .tmp sia ignorato; completarlo e rinominarlo .xml. Ripetere con XML presente prima dell’avvio.','Il .tmp non avvia il prelievo. L’XML completo viene elaborato; anche quello presente al riavvio viene considerato, senza duplicare l’addebito.'),
('TC_28','Pagina','Uso da tastiera e schermo piccolo','Browser; larghezza circa 375 px; cliente di prova.','Compilare il modulo con Tab e tastiera; selezionare gli importi; provocare un errore e leggerlo.','Campi etichettati e focus visibile; radio utilizzabili; messaggi leggibili; nessun campo o pulsante tagliato sullo schermo piccolo.'),
('TC_29','TIBCO / rete','Cartella condivisa fra due computer','Servizio e BW 6 su host diversi; condivisione UNC; utenti dei servizi autorizzati.','Configurare i percorsi sullo stesso spazio condiviso; inviare la richiesta e verificare lettura e spostamento.','TIBCO vede solo l’XML completo e lo archivia correttamente. Un problema di permessi produce un errore gestito, senza doppio addebito.'),
]


def column(n):
    out = ''
    while n:
        n, mod = divmod(n - 1, 26)
        out = chr(65 + mod) + out
    return out


def cell(ref, value='', style=0, formula=None, cached=None):
    if formula is not None:
        return f'<c r="{ref}" s="{style}"><f>{escape(formula)}</f><v>{cached or 0}</v></c>'
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{escape(str(value))}</t></is></c>'


def make_xlsx():
    last = 4 + len(cases)
    headers = ['ID', 'Ambito', 'Scenario', 'Dati / condizioni iniziali', 'Passi da eseguire', 'Risultato atteso', 'Risultato ottenuto', 'Esito', 'Data prova', 'Note / evidenze']
    rows = [f'<row r="1" ht="29" customHeight="1">{cell("A1", "Progetto ATM – Casi di test", 1)}</row>', f'<row r="2" ht="32" customHeight="1">{cell("A2", "Piano delle prove: nessun test è ancora registrato come eseguito. Compilare le colonne G–J durante il collaudo.", 3)}</row>', '<row r="3"/>', '<row r="4" ht="30" customHeight="1">' + ''.join(cell(f'{column(i)}4', v, 2) for i, v in enumerate(headers, 1)) + '</row>']
    for index, item in enumerate(cases, 5):
        values = [*item, '', 'Da eseguire', '', '']
        cells = []
        for n, value in enumerate(values, 1):
            style = 5 if n == 8 else 6 if n == 9 else 7 if n in (7, 10) else 4
            cells.append(cell(f'{column(n)}{index}', value, style))
        rows.append(f'<row r="{index}" ht="116" customHeight="1">{"".join(cells)}</row>')
    widths = [12, 19, 27, 43, 47, 60, 40, 18, 15, 35]
    cols = ''.join(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths, 1))
    sheet = f'''{XML}<worksheet xmlns="{S}" xmlns:r="{R}"><dimension ref="A1:J{last}"/><sheetViews><sheetView workbookViewId="0" zoomScale="85"><pane xSplit="3" ySplit="4" topLeftCell="D5" activePane="bottomRight" state="frozen"/><selection pane="bottomRight" activeCell="G5" sqref="G5"/></sheetView></sheetViews><sheetFormatPr defaultRowHeight="18"/><cols>{cols}</cols><sheetData>{''.join(rows)}</sheetData><mergeCells count="2"><mergeCell ref="A1:J1"/><mergeCell ref="A2:J2"/></mergeCells>
    <conditionalFormatting sqref="H5:H{last}"><cfRule type="cellIs" dxfId="0" priority="1" operator="equal"><formula>"Superato"</formula></cfRule><cfRule type="cellIs" dxfId="1" priority="2" operator="equal"><formula>"Non superato"</formula></cfRule><cfRule type="cellIs" dxfId="2" priority="3" operator="equal"><formula>"Bloccato"</formula></cfRule></conditionalFormatting>
    <dataValidations count="1"><dataValidation type="list" allowBlank="0" showErrorMessage="1" errorTitle="Esito non valido" error="Scegli un esito dall’elenco." sqref="H5:H{last}"><formula1>"Da eseguire,Superato,Non superato,Bloccato"</formula1></dataValidation></dataValidations><printOptions horizontalCentered="1"/><pageMargins left="0.2" right="0.2" top="0.4" bottom="0.4" header="0.2" footer="0.2"/><pageSetup paperSize="8" orientation="landscape" fitToWidth="1" fitToHeight="0"/><headerFooter><oddFooter>&amp;LProgetto ATM&amp;RPagina &amp;P di &amp;N</oddFooter></headerFooter><tableParts count="1"><tablePart r:id="rIdTable"/></tableParts></worksheet>'''
    # Attivare il ridimensionamento per la stampa senza cambiare la vista del foglio.
    sheet = sheet.replace('<dimension', '<sheetPr><pageSetUpPr fitToPage="1"/></sheetPr><dimension', 1)
    instructions = [
        ('Progetto ATM – Come compilare i test', '', 'title'),
        ('Stato iniziale', 'La tabella contiene 29 prove pianificate, non risultati di un collaudo eseguito.', ''),
        ('1. Preparazione', 'Usare clienti fittizi. Reimpostare saldo, cartelle e registro di prova come indicato in ogni caso. Non usare dati reali.', ''),
        ('2. Esecuzione', 'Seguire i passi del caso. Controllare messaggi, popup, XML e prenotazioni. Per TIBCO controllare anche esito, addebito e archiviazione.', ''),
        ('3. Risultato ottenuto', 'Scrivere ciò che è successo davvero. Se un caso contiene più varianti, provarle tutte e indicare eventuali differenze.', ''),
        ('4. Esito', 'Usare l’elenco a discesa: Da eseguire, Superato, Non superato oppure Bloccato. Un caso è superato solo se tutti i risultati attesi sono verificati.', ''),
        ('5. Data e note', 'Inserire la data della prova e un riferimento alle evidenze: nome del file XML, identificativo, schermata o log senza PIN.', ''),
        ('6. TIBCO non disponibile', 'Lasciare Da eseguire oppure indicare Bloccato con il motivo. Un consumer simulato non dimostra che il processo BW 6 funzioni.', ''),
        ('Dati principali', 'Mario Rossi, PIN 12345. Saldo 500 € nelle prove positive, salvo diversa indicazione; saldo 100 € per TC_04.', ''),
        ('Secondo cliente', 'Èlia D’Amico-Rossi, PIN 01234, saldo 500 €. Aggiungere un cliente con apostrofo semplice per la seconda variante di TC_12.', ''),
        ('Documenti collegati', 'Documenti_progetto_ATM.docx: BUR e FUD. TAD_Architettura_Tecnica_ATM.docx: scelte tecniche e processo previsto.', ''),
        ('Significato del popup', '“Prelevare il denaro entro 30 secondi” conferma il salvataggio dell’XML. L’elaborazione centrale va verificata separatamente.', ''),
        ('Saldo della demo', 'Disponibilità = saldo iniziale meno prenotazioni. TIBCO non scala di nuovo il saldo locale; gestisce il proprio archivio centrale di prova.', ''),
        ('Filtri e stampa', 'Usare i filtri sulla riga 4 per esito o ambito. Intestazioni e prime tre colonne sono bloccate. Stampa impostata su A3 orizzontale.', ''),
        ('Riepilogo degli esiti', '', 'header'),
        ('Totale casi', '', 'total'),
        ('Da eseguire', '', 'count'),
        ('Superato', '', 'count'),
        ('Non superato', '', 'count'),
        ('Bloccato', '', 'count'),
    ]
    guide_rows = []
    for n, (label, value, kind) in enumerate(instructions, 1):
        if kind == 'title':
            content = cell(f'A{n}', label, 1)
        elif kind == 'header':
            content = cell(f'A{n}', label, 2) + cell(f'B{n}', '', 2)
        elif kind in ('count', 'total'):
            formula = f"COUNTA('Casi di test'!A5:A{last})" if kind == 'total' else f'COUNTIF(\'Casi di test\'!H5:H{last},A{n})'
            content = cell(f'A{n}', label, 4) + cell(f'B{n}', style=4, formula=formula, cached=len(cases) if kind == 'total' or label == 'Da eseguire' else 0)
        else:
            content = cell(f'A{n}', label, 4) + cell(f'B{n}', value, 4)
        height = 30 if kind else 48
        guide_rows.append(f'<row r="{n}" ht="{height}" customHeight="1">{content}</row>')
    guide = f'{XML}<worksheet xmlns="{S}"><dimension ref="A1:B20"/><sheetViews><sheetView workbookViewId="0"/></sheetViews><sheetFormatPr defaultRowHeight="18"/><cols><col min="1" max="1" width="27" customWidth="1"/><col min="2" max="2" width="110" customWidth="1"/></cols><sheetData>{"".join(guide_rows)}</sheetData><mergeCells count="1"><mergeCell ref="A1:B1"/></mergeCells><pageMargins left="0.3" right="0.3" top="0.4" bottom="0.4" header="0.2" footer="0.2"/><pageSetup paperSize="9" orientation="landscape" fitToWidth="1" fitToHeight="1"/></worksheet>'
    styles = f'''{XML}<styleSheet xmlns="{S}"><fonts count="3"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="16"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font><font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts><fills count="5"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF203A53"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFF2F5F8"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFFFF8DC"/><bgColor indexed="64"/></patternFill></fill></fills><borders count="2"><border/><border><left style="thin"><color rgb="FFD8DEE5"/></left><right style="thin"><color rgb="FFD8DEE5"/></right><top style="thin"><color rgb="FFD8DEE5"/></top><bottom style="thin"><color rgb="FFD8DEE5"/></bottom></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="8"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf><xf numFmtId="0" fontId="2" fillId="2" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf><xf numFmtId="0" fontId="0" fillId="3" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf><xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf><xf numFmtId="0" fontId="0" fillId="4" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" horizontal="center" wrapText="1"/></xf><xf numFmtId="14" fontId="0" fillId="4" borderId="1" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="top"/></xf><xf numFmtId="0" fontId="0" fillId="4" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles><dxfs count="3"><dxf><fill><patternFill patternType="solid"><fgColor rgb="FFC6EFCE"/><bgColor rgb="FFC6EFCE"/></patternFill></fill></dxf><dxf><fill><patternFill patternType="solid"><fgColor rgb="FFFFC7CE"/><bgColor rgb="FFFFC7CE"/></patternFill></fill></dxf><dxf><fill><patternFill patternType="solid"><fgColor rgb="FFFFEB9C"/><bgColor rgb="FFFFEB9C"/></patternFill></fill></dxf></dxfs><tableStyles count="0" defaultTableStyle="TableStyleMedium2" defaultPivotStyle="PivotStyleLight16"/></styleSheet>'''
    table = f'{XML}<table xmlns="{S}" id="1" name="TabellaTestATM" displayName="TabellaTestATM" ref="A4:J{last}" totalsRowShown="0"><autoFilter ref="A4:J{last}"/><tableColumns count="10">' + ''.join(f'<tableColumn id="{i}" name="{escape(h)}"/>' for i, h in enumerate(headers, 1)) + '</tableColumns><tableStyleInfo name="TableStyleMedium2" showFirstColumn="0" showLastColumn="0" showRowStripes="1" showColumnStripes="0"/></table>'
    workbook = f'{XML}<workbook xmlns="{S}" xmlns:r="{R}"><bookViews><workbookView activeTab="0"/></bookViews><sheets><sheet name="Casi di test" sheetId="1" r:id="rId1"/><sheet name="Istruzioni" sheetId="2" r:id="rId2"/></sheets><definedNames><definedName name="_xlnm.Print_Titles" localSheetId="0">\'Casi di test\'!$4:$4</definedName><definedName name="_xlnm.Print_Area" localSheetId="0">\'Casi di test\'!$A$1:$J${last}</definedName></definedNames><calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>'
    overrides = [('workbook.xml','spreadsheetml.sheet.main'),('styles.xml','spreadsheetml.styles'),('worksheets/sheet1.xml','spreadsheetml.worksheet'),('worksheets/sheet2.xml','spreadsheetml.worksheet'),('tables/table1.xml','spreadsheetml.table')]
    types = f'{XML}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>' + ''.join(f'<Override PartName="/xl/{p}" ContentType="application/vnd.openxmlformats-officedocument.{t}+xml"/>' for p,t in overrides) + '</Types>'
    with ZipFile(OUT / 'Casi_di_test_ATM.xlsx', 'w', ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', types)
        z.writestr('_rels/.rels', f'{XML}<Relationships xmlns="{P}"><Relationship Id="rId1" Type="{R}/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml', workbook)
        z.writestr('xl/styles.xml', styles)
        z.writestr('xl/worksheets/sheet1.xml', sheet)
        z.writestr('xl/worksheets/sheet2.xml', guide)
        z.writestr('xl/tables/table1.xml', table)
        z.writestr('xl/_rels/workbook.xml.rels', f'{XML}<Relationships xmlns="{P}"><Relationship Id="rId1" Type="{R}/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="{R}/worksheet" Target="worksheets/sheet2.xml"/><Relationship Id="rId3" Type="{R}/styles" Target="styles.xml"/></Relationships>')
        z.writestr('xl/worksheets/_rels/sheet1.xml.rels', f'{XML}<Relationships xmlns="{P}"><Relationship Id="rIdTable" Type="{R}/table" Target="../tables/table1.xml"/></Relationships>')


make_xlsx()
for file in sorted(OUT.iterdir()):
    if file.suffix in ('.docx', '.xlsx'):
        with ZipFile(file) as z:
            assert z.testzip() is None, file.name
            for name in z.namelist():
                if name.endswith(('.xml', '.rels')):
                    ET.fromstring(z.read(name))
        print(f'Creato e verificato XML: {file.name}')
