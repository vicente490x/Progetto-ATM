"""Real Chromium DOM + File System API tests. OS picker replaced with OPFS.
Archive outcomes are fixtures, not a TIBCO execution.
"""
import json, os, threading, uuid, hashlib
from pathlib import Path
from datetime import datetime, timezone
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
from lxml import etree
SCHEMA = None

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'test-results';OUT.mkdir(exist_ok=True)
class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT/'public')))
threading.Thread(target=server.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{server.server_port}'
results=[]
SCHEMA=etree.XMLSchema(etree.parse(str(ROOT/'ProgettoATM/Schemas/TransazioneATM.xsd')))
def validate_xml(p):
    for name,text in files(p):SCHEMA.assertValid(etree.fromstring(text.encode()))

def fill(p,pin='12345',name='Mario',surname='Rossi',amount=None):
    p.locator('[name=nome]').fill(name);p.locator('[name=cognome]').fill(surname)
    p.locator('[name=pin]').evaluate('(e,v)=>e.value=v',pin)
    if amount is not None:
        p.locator('[value=altro]').check();p.locator('#custom-amount').fill(amount)

def send(p):p.locator('button[type=submit]').click()
def status(p):return p.locator('#status').inner_text()
def files(p):return p.evaluate('''async()=>{const d=await window.testRoot.getDirectoryHandle('input');let a=[];for await(const [n,h] of d.entries())a.push([n,await(await h.getFile()).text()]);return a;}''')
def archive(p,folder='processed',content=None):
    p.evaluate('''async([folder,content])=>{const d=await window.testRoot.getDirectoryHandle('input');for await(const [n,h] of d.entries()){const data=content??await(await h.getFile()).text();const a=await window.testRoot.getDirectoryHandle(folder);const s=await(await a.getFileHandle(n,{create:true})).createWritable();await s.write(data);await s.close();}}''',[folder,content])
def wait_saved(p):p.wait_for_function("document.querySelector('#status').textContent.includes('inviata')")
def check(x,m):assert x,m

def standard(p):
    fill(p);send(p);wait_saved(p);a=files(p);check(len(a)==1,'Un XML');check('<Importo>50</Importo>' in a[0][1],'Importo 50');uuid.UUID(a[0][0][:-4]);check('eseguito da TIBCO' not in status(p),'Nessun falso successo');validate_xml(p)

def invalid_pin(p):
    for pin in ['123','12a45','123456']:
        fill(p,pin=pin);send(p);check('5 cifre' in status(p),'Rifiuto PIN '+pin);check(files(p)==[],'Nessun XML')

def custom(p):fill(p,amount='80');send(p);wait_saved(p);check('<Importo>80</Importo>' in files(p)[0][1],'Importo libero')
def names(p):
    for n,s in [('', 'Rossi'),('Mario',''),('  ','  ')]:
        fill(p,name=n,surname=s);send(p);check('nome e cognome validi' in status(p),'Campi obbligatori');check(files(p)==[],'Nessun XML')

def unicode(p):
    fill(p,pin='01234',name=' Èlia ',surname=' D’Amico-Rossi ');send(p);wait_saved(p);x=files(p)[0][1]
    check('<Nome>Èlia</Nome>' in x and '<Cognome>D’Amico-Rossi</Cognome>' in x and '<PIN>01234</PIN>' in x,'Unicode e zero iniziale')
    archive(p);p.locator('#check-status').click();p.locator('#next-request').click();fill(p,name=" Anna Maria ",surname=" O'Connor ");send(p);wait_saved(p)
    texts=[v for n,v in files(p)];check(any('<Nome>Anna Maria</Nome>' in v and '<Cognome>O&apos;Connor</Cognome>' in v for v in texts),'Apostrofo semplice e nome composto');validate_xml(p)

def amounts(p):
    for value in ['', '0','-10','abc','NaN','Infinity','1e2','10.001']:
        fill(p,amount=value);send(p);check('importo positivo' in status(p),'Importo rifiutato '+value);check(files(p)==[],'Nessun file')

def decimals(p):
    for value in ['80,50','80.50']:
        fill(p,amount=value);send(p);wait_saved(p);check('<Importo>80.50</Importo>' in files(p)[-1][1],'Decimali normalizzati')
        archive(p);p.locator('#check-status').click();p.locator('#next-request').click()

def escaping(p):
    value='A & <B> "C" \'D\'';fill(p,name=value);send(p);wait_saved(p)
    actual=p.evaluate('x=>new DOMParser().parseFromString(x,"application/xml").querySelector("Nome").textContent',files(p)[0][1]);check(actual==value,'Roundtrip XML')

def reload(p):
    fill(p);send(p);wait_saved(p);id=p.evaluate("localStorage.getItem('atm.pending')");p.reload();p.locator('#connect').click();check(p.locator('[type=submit]').is_disabled(),'No nuovo invio dopo reload');check(p.evaluate("localStorage.getItem('atm.pending')")==id,'UUID conservato');check(len(files(p))==1,'Un file')

def double(p):
    fill(p,amount='80');p.locator('[value="100"]').check();p.locator('[type=submit]').evaluate('e=>{e.click();e.click()}');wait_saved(p)
    check(len(files(p))==1,'Un invio');check('<Importo>100</Importo>' in files(p)[0][1],'Radio prevale');check(p.locator('[type=submit]').is_disabled(),'Blocco in attesa')

def outcome(p):
    fill(p);send(p);wait_saved(p);p.locator('#check-status').click();p.wait_for_function("document.querySelector('#status').textContent.includes('non ancora disponibile')");check('non ancora disponibile' in status(p),'Attesa');archive(p);p.locator('#check-status').click();p.wait_for_function("document.querySelector('#status').textContent.includes('eseguito da TIBCO')");check('eseguito da TIBCO' in status(p),'Conferma archivio');check(p.locator('[name=pin]').input_value()=='','PIN cancellato');p.locator('#next-request').click();check(not p.locator('[type=submit]').is_disabled(),'Nuova richiesta esplicita')

def conflict(p):
    fill(p);send(p);wait_saved(p);archive(p,content='contenuto differente');p.locator('#check-status').click();p.wait_for_function("document.querySelector('#status').textContent.includes('contenuto diverso')");check('contenuto diverso' in status(p),'Conflitto archivio');check(p.locator('#next-request').is_disabled(),'Nessuna nuova richiesta')

def write_failure(p):
    p.evaluate("() => { FileSystemFileHandle.prototype.createWritable=async()=>{throw new DOMException('Scrittura negata','NotAllowedError')}; }")
    fill(p);send(p);p.wait_for_function("document.querySelector('#status').textContent.includes('non confermato')");check(p.locator('[type=submit]').is_disabled(),'Esito incerto blocca nuovo ID');check(p.evaluate("!!localStorage.getItem('atm.pending')"),'UUID conservato')

def layout(p):
    p.set_viewport_size({'width':375,'height':812});check(p.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Nessun overflow orizzontale')
    p.locator('[name=nome]').focus();p.keyboard.press('Tab');check(p.locator('[name=cognome]').evaluate('e=>e===document.activeElement'),'Ordine tastiera');p.screenshot(path=str(OUT/'frontend-375.png'),full_page=True)

def two_ids(p):
    fill(p);send(p);wait_saved(p);first=files(p)[0][0];archive(p);p.locator('#check-status').click();p.locator('#next-request').click();fill(p);send(p);wait_saved(p);check(len({n for n,x in files(p)})==2,'UUID distinti');validate_xml(p)

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    for id,title,fn in [('FE01','XML standard',standard),('FE02','PIN non valido',invalid_pin),('FE03','Importo libero',custom),('FE04','Campi vuoti',names),('FE05','Unicode e PIN zero',unicode),('FE06','Importi non validi',amounts),('FE07','Decimali',decimals),('FE08','Escape XML',escaping),('FE09','Ripresa dopo reload',reload),('FE10','Radio e doppio invio',double),('FE11','Conferma archivio',outcome),('FE12','Conflitto archivio',conflict),('FE13','Errore scrittura iniettato',write_failure),('FE14','Layout e tastiera',layout),('FE15','UUID distinti',two_ids)]:
        context=browser.new_context();page=context.new_page()
        page.add_init_script('window.showDirectoryPicker=async()=>{window.testRoot=await navigator.storage.getDirectory();return window.testRoot;}')
        try:
            page.goto(URL);page.locator('#connect').click();page.wait_for_function("!document.querySelector('[type=submit]').disabled");fn(page)
            r={'id':id,'scenario':title,'esito':'Superato','dettaglio':'Asserzioni eseguite in Chromium con filesystem OPFS reale; picker e archiviazione di esito controllati dal test.'}
        except Exception as e:r={'id':id,'scenario':title,'esito':'Non superato','dettaglio':str(e)}
        results.append(r);print(json.dumps(r,ensure_ascii=False),flush=True);context.close()
    report={'data_utc':datetime.now(timezone.utc).isoformat(),'commit':os.getenv('GITHUB_SHA'),'chromium':browser.version,'app_sha256':hashlib.sha256((ROOT/'public/app.js').read_bytes()).hexdigest(),'scope':'Browser reale e OPFS; nessun picker OS o motore TIBCO','risultati':results};browser.close()
server.shutdown()
(OUT/'browser.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print('REPORT_BROWSER_JSON='+json.dumps(report,ensure_ascii=False),flush=True)
raise SystemExit(any(r['esito']!='Superato' for r in results))
