'use strict';
const form = document.querySelector('#withdrawal-form');
const customAmount = document.querySelector('#custom-amount');
const chosenAmount = document.querySelector('#chosen-amount');
const status = document.querySelector('#status');
const connect = document.querySelector('#connect');
const checkStatus = document.querySelector('#check-status');
const nextRequest = document.querySelector('#next-request');
const submit = form.querySelector('[type=submit]');
let folders = null;
// Only the request ID is persisted, never the PIN or personal details.
const savedId = localStorage.getItem('atm.pending');
let request = /^[0-9a-f-]{36}$/.test(savedId || '') ? {id: savedId, xml: null} : null;
let busy = false;
const esc = value => value.replace(/[<>&"']/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&apos;'}[c]));
function show(message, kind = '') { status.textContent = message; status.className = `status ${kind}`; }
function amount() { return form.elements.sceltaImporto.value === 'altro' ? customAmount.value.trim() : form.elements.sceltaImporto.value; }
function refresh() {
  customAmount.disabled = form.elements.sceltaImporto.value !== 'altro';
  chosenAmount.textContent = `Importo selezionato: ${amount() || 'da inserire'} €`;
  submit.disabled = busy || !folders || !!request;
  checkStatus.disabled = busy || !folders || !request;
  connect.disabled = busy || !!folders;
}
async function read(folder, id) {
  try { return await (await (await folder.getFileHandle(`${id}.xml`)).getFile()).text(); }
  catch (e) { if (e.name === 'NotFoundError') return null; throw e; }
}
async function outcome() {
  const ok = await read(folders.processed, request.id);
  const ko = await read(folders.error, request.id);
  if (ok !== null && ko !== null) throw Error('Esiti discordanti: verificare la richiesta in TIBCO.');
  const archived = ok ?? ko;
  if (archived !== null && request.xml && archived !== request.xml) throw Error('ID già presente con contenuto diverso: verificare TIBCO.');
  if (archived !== null) {
    show(`Richiesta ${request.id}: ${ok !== null ? 'prelievo eseguito da TIBCO.' : 'richiesta rifiutata. Consultare il log TIBCO per il motivo.'}`, ok !== null ? 'ok' : 'error');
    nextRequest.disabled = false;
    request.xml = null;
    form.elements.pin.value = '';
    return true;
  }
  show(`Richiesta ${request.id}: esito non ancora disponibile. Non inviare un altro prelievo; controlla TIBCO e riprova il controllo.`);
  return false;
}
connect.addEventListener('click', async () => {
  if (!window.showDirectoryPicker) return show('Apri questa pagina con Chrome o Edge su PC: serve l’accesso alle cartelle locali.', 'error');
  busy = true; refresh();
  try {
    const root = await window.showDirectoryPicker({mode: 'readwrite'});
    folders = {};
    for (const name of ['input','processed','error']) folders[name] = await root.getDirectoryHandle(name, {create: true});
    show('Cartella collegata. Verifica che il File Poller TIBCO legga la sottocartella input.');
    if (request) await outcome();
  } catch (e) { folders = null; show(`Collegamento non riuscito: ${e.message}`, 'error'); }
  finally { busy = false; refresh(); }
});
form.addEventListener('change', refresh);
customAmount.addEventListener('input', refresh);
form.addEventListener('submit', async event => {
  event.preventDefault();
  if (busy || request || !folders) return;
  const nome = form.elements.nome.value.trim(), cognome = form.elements.cognome.value.trim(), pin = form.elements.pin.value;
  const raw = amount().replace(',', '.');
  if (!nome || !cognome || nome.length > 100 || cognome.length > 100 || /[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(nome+cognome)) return show('Inserisci nome e cognome validi (massimo 100 caratteri).', 'error');
  if (!/^[0-9]{5}$/.test(pin)) return show('Il PIN deve contenere 5 cifre.', 'error');
  if (!/^(0|[1-9]\d{0,9})(\.\d{1,2})?$/.test(raw) || Number(raw) <= 0) return show('Inserisci un importo positivo con massimo due decimali.', 'error');
  busy = true;
  request = {id: crypto.randomUUID(), xml: `<?xml version="1.0" encoding="UTF-8"?>\n<TransazioneATM><Cliente><Nome>${esc(nome)}</Nome><Cognome>${esc(cognome)}</Cognome><PIN>${pin}</PIN></Cliente><DettagliPrelievo><Importo>${raw}</Importo><DataOra>${new Date().toISOString()}</DataOra></DettagliPrelievo></TransazioneATM>\n`};
  refresh();
  try {
    // Persist BEFORE publication, so reloading after an uncertain write cannot issue a new debit.
    localStorage.setItem('atm.pending', request.id);
    const handle = await folders.input.getFileHandle(`${request.id}.xml`, {create: true});
    const stream = await handle.createWritable();
    await stream.write(request.xml);
    await stream.close();
    show(`Richiesta ${request.id} inviata. Il prelievo sarà confermato solo dopo l’elaborazione TIBCO.`);
  } catch (e) { show(`Invio non confermato (${request.id}): ${e.message}. Verifica la cartella input e TIBCO prima di una nuova richiesta.`, 'error'); }
  finally { busy = false; refresh(); }
});
checkStatus.addEventListener('click', async () => {
  if (busy || !folders || !request) return;
  busy = true; refresh();
  try { await outcome(); } catch(e) { show(e.message, 'error'); }
  finally { busy = false; refresh(); }
});
nextRequest.addEventListener('click', () => {
  if (nextRequest.disabled || busy) return;
  localStorage.removeItem('atm.pending'); request = null;
  nextRequest.disabled = true; show('Puoi inserire un nuovo prelievo.'); refresh();
});
if (request) show(`Richiesta ${request.id} da verificare. Collega la stessa cartella per recuperare l’esito.`);
refresh();
