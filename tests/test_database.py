"""Test the exact JDBC statement embedded in the BWP against an isolated PostgreSQL.

Never use a user database. Requires a fresh database with no public tables.
Does not emulate or certify the TIBCO engine.
"""
import os, json, uuid, hashlib, time
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import psycopg
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
DSN = os.environ['ATM_TEST_DSN']
BWP = ROOT / 'ProgettoATM/Processes/progettoatm/ATMCompleto.bwp'
tree = etree.parse(str(BWP))
statements = tree.xpath('//*[@sqlStatement]/@sqlStatement')
assert len(statements) == 1
SQL = statements[0].replace('?', '%s')
schema = etree.XMLSchema(etree.parse(str(ROOT/'ProgettoATM/Schemas/TransazioneATM.xsd')))
results = []

def connect():
    return psycopg.connect(DSN, autocommit=True)

def setup():
    with connect() as c:
        assert c.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'").fetchone()[0] == 0, 'Use a fresh isolated database'
        c.execute((ROOT/'database/01_creazione_tabelle.sql').read_text())

def reset(balance=50000):
    with connect() as c:
        c.execute('TRUNCATE public.transazioni, public.clienti RESTART IDENTITY')
        c.execute('INSERT INTO public.clienti(nome,cognome,pin,saldo_centesimi) VALUES(%s,%s,%s,%s)', ('Mario','Rossi','12345',balance))
        c.execute('INSERT INTO public.clienti(nome,cognome,pin,saldo_centesimi) VALUES(%s,%s,%s,%s)', ('Èlia',"D’Amico-Rossi",'01234',50000))

def request(amount=5000, id=None, name='Mario', surname='Rossi', pin='12345', conn=None):
    params=(id or str(uuid.uuid4()),name,surname,pin,amount)
    if conn is not None: return conn.execute(SQL,params).fetchone()
    with connect() as c: return c.execute(SQL,params).fetchone()

def state():
    with connect() as c:
        return c.execute('SELECT saldo_centesimi FROM public.clienti ORDER BY id').fetchall(), c.execute('SELECT stato,importo_centesimi FROM public.transazioni ORDER BY creata_il,id_richiesta').fetchall()

def run(id, title, fn):
    start=time.monotonic()
    try:
        reset(); detail=fn(); result={'id':id,'scenario':title,'esito':'Superato','dettaglio':detail or 'Asserzioni superate'}
    except Exception as e: result={'id':id,'scenario':title,'esito':'Non superato','dettaglio':str(e)}
    result['durata_ms']=round((time.monotonic()-start)*1000);results.append(result)
    print(json.dumps(result,ensure_ascii=False),flush=True)

def check(condition, message):
    assert condition, message

def normal():
    check(request()==('OK',45000),'Saldo dopo 50 EUR')
    check(state()==([(45000,),(50000,)],[('ESEGUITA',5000)]),'Saldo e storico coerenti')
    return '50000 -> 45000 centesimi; una ESEGUITA da 5000'

def insufficient():
    check(request(60000)==('SALDO_INSUFFICIENTE',50000),'Esito saldo insufficiente')
    check(state()==([(50000,),(50000,)],[('RIFIUTATA',60000)]),'Saldo invariato e rifiuto registrato')

def credentials():
    for kwargs in [{'pin':'54321'},{'name':'Sconosciuto'},{'pin':"' OR 1=1 --"}]:
        check(request(**kwargs)[0]=='CLIENTE_NON_VALIDO','Credenziali respinte')
    check(state()==([(50000,),(50000,)],[]),'Nessuna modifica con credenziali errate')

def retry():
    id=str(uuid.uuid4());check(request(id=id)[0]=='OK','Primo invio'); before=state()
    check(request(id=id)[0]=='GIA_ELABORATA','Replay');check(state()==before,'Nessun doppio addebito')

def conflict():
    id=str(uuid.uuid4());request(id=id);before=state()
    check(request(6000,id=id)[0]=='CONFLITTO_ID','Importo diverso')
    check(request(id=id,name='Èlia',surname='D’Amico-Rossi',pin='01234')[0]=='CONFLITTO_ID','Cliente diverso')
    check(state()==before,'Conflitto non modifica saldo/storico')

def exact():
    reset(10000);check(request(10000)==('OK',0),'Saldo esatto');check(request(1)==('SALDO_INSUFFICIENTE',0),'Saldo zero')

def pending():
    with connect() as c: c.execute("INSERT INTO transazioni(id_richiesta,cliente_id,importo_centesimi) VALUES(%s,1,1000)",(str(uuid.uuid4()),))
    before=state();check(request()[0]=='RICHIESTA_DA_VERIFICARE','Prenotazione precedente');check(state()==before,'Prenotazione non toccata')

def concurrent(same_id=False, different_client=False):
    reset(10000);barrier=Barrier(2);id=str(uuid.uuid4())
    def work(i):
        with connect() as c:
            barrier.wait(timeout=10)
            args={'amount':8000,'id':id if same_id else str(uuid.uuid4()),'conn':c}
            if different_client and i:args.update(name='Èlia',surname='D’Amico-Rossi',pin='01234')
            return request(**args)[0]
    with ThreadPoolExecutor(max_workers=2) as ex: out=list(ex.map(work,range(2)))
    balances,trans=state();executed=[t for t in trans if t[0]=='ESEGUITA']
    check(len(executed)==1,'Un solo addebito concorrente: '+str((out,balances,trans)))
    check(sum(b[0] for b in balances)==52000,'Conservazione saldo: '+str(balances))
    if not same_id:check(sorted(out)==['OK','SALDO_INSUFFICIENTE'],'Una accettata e una rifiutata')
    if same_id and not different_client:check(request(8000,id=id)[0]=='GIA_ELABORATA','Replay dopo concorrenza')
    return f'Esiti {out}; saldi {balances}; storico {trans}'

def rollback():
    with connect() as c:
        # Fault injection only in the disposable database.
        c.execute("ALTER TABLE clienti ADD CONSTRAINT force_failure CHECK(saldo_centesimi >= 50000)")
    try:
        try:request();raise AssertionError('Addebito doveva fallire')
        except psycopg.errors.CheckViolation:pass
        check(state()==([(50000,),(50000,)],[]),'Rollback anche dello storico')
    finally:
        with connect() as c:c.execute('ALTER TABLE clienti DROP CONSTRAINT force_failure')

def persistence():
    id=str(uuid.uuid4());reset(10000);request(8000,id=id)
    check(request(8000,id=id)[0]=='GIA_ELABORATA','Nuova connessione legge commit precedente')
    check(request(5000)[0]=='SALDO_INSUFFICIENTE','Saldo persistente')

def rejected_retry():
    id=str(uuid.uuid4());request(60000,id=id)
    with connect() as c:c.execute('UPDATE clienti SET saldo_centesimi=100000 WHERE id=1')
    check(request(60000,id=id)[0]=='RIFIUTATA','UUID rifiutato non riattivato');check(state()[0][0][0]==100000,'Nessun addebito tardivo')

def xml_validation():
    def xml(pin='<PIN>01234</PIN>',amount='80.50',name='Èlia'):
        return f'<TransazioneATM><Cliente><Nome>{name}</Nome><Cognome>D’Amico-Rossi</Cognome>{pin}</Cliente><DettagliPrelievo><Importo>{amount}</Importo><DataOra>2026-10-21T20:00:00+02:00</DataOra></DettagliPrelievo></TransazioneATM>'.encode()
    schema.assertValid(etree.fromstring(xml()))
    for pin in ['', '<PIN>123</PIN>','<PIN>12a45</PIN>','<PIN>123456</PIN>']:
        check(not schema.validate(etree.fromstring(xml(pin=pin))),'XSD deve rifiutare '+pin)
    for a in ['0','-10','abc','NaN','Infinity','1e2','10.001']:
        check(not schema.validate(etree.fromstring(xml(amount=a))),'XSD deve rifiutare '+a)

setup()
with connect() as c: version=c.execute('SELECT version()').fetchone()[0]
run('DB01','Prelievo standard',normal)
run('DB02','Saldo insufficiente',insufficient)
run('DB03','Credenziali e input SQL ostile',credentials)
run('DB04','Ripetizione UUID',retry)
run('DB05','Conflitto UUID',conflict)
run('DB06','Disponibilità esatta',exact)
run('DB07','Prenotazioni precedenti',pending)
run('DB08','Richieste concorrenti',lambda:concurrent())
run('DB09','UUID concorrente stesso cliente',lambda:concurrent(True))
run('DB10','UUID concorrente clienti diversi',lambda:concurrent(True,True))
run('DB11','Rollback atomico',rollback)
run('DB12','Persistenza tra connessioni',persistence)
run('DB13','Replay di richiesta rifiutata',rejected_retry)
run('DB14','PIN iniziale e nominativo Unicode',lambda:check(request(name=' Èlia ',surname=' D’Amico-Rossi ',pin='01234')==('OK',45000),'Unicode e trim'))
run('DB15','Importo 80 euro',lambda:check(request(8000)==('OK',42000),'Importo libero'))
run('DB16','Importo 80.50 euro',lambda:check(request(8050)==('OK',41950),'Centesimi esatti'))
run('XSD01','Validazione contratto XML',xml_validation)
report={'data_utc':datetime.now(timezone.utc).isoformat(),'commit':os.getenv('GITHUB_SHA'),'postgresql':version,'bwp_sha256':hashlib.sha256(BWP.read_bytes()).hexdigest(),'scope':'Query JDBC estratta dal BWP su PostgreSQL reale; nessun runtime TIBCO','risultati':results}
(ROOT/'test-results').mkdir(exist_ok=True)
(ROOT/'test-results/database.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print('REPORT_JSON='+json.dumps(report,ensure_ascii=False),flush=True)
raise SystemExit(any(x['esito']!='Superato' for x in results))
