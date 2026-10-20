const form = document.querySelector('#withdrawal-form');
const customAmount = document.querySelector('#custom-amount');
const chosenAmount = document.querySelector('#chosen-amount');
const status = document.querySelector('#status');
const checkStatus = document.querySelector('#check-status');
let pendingRequest = null;
let lastSavedId = null;

function selectedAmount() {
  const choice = form.elements.sceltaImporto.value;
  return choice === 'altro' ? customAmount.value.trim() : choice;
}

function updateAmount() {
  customAmount.disabled = form.elements.sceltaImporto.value !== 'altro';
  const amount = selectedAmount();
  chosenAmount.textContent = `Importo selezionato: ${amount || 'da inserire'} €`;
}

function showStatus(message, kind = '') {
  status.textContent = message;
  status.className = `status ${kind}`;
}

form.addEventListener('change', updateAmount);
customAmount.addEventListener('input', updateAmount);
updateAmount();

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const nome = form.elements.nome.value.trim();
  const cognome = form.elements.cognome.value.trim();
  const pin = form.elements.pin.value;
  const importo = selectedAmount();
  if (!nome || !cognome) return showStatus('Inserisci nome e cognome', 'error');
  if (!/^[0-9]{5}$/.test(pin)) return showStatus('Il PIN deve essere di 5 cifre', 'error');
  if (!/^(?:0|[1-9]\d*)(?:[.,]\d{1,2})?$/.test(importo) || Number(importo.replace(',', '.')) <= 0) {
    return showStatus('Inserisci un importo positivo con al massimo due decimali', 'error');
  }
  const data = { nome, cognome, pin, importo };
  const signature = JSON.stringify(data);
  if (!pendingRequest || pendingRequest.signature !== signature) {
    pendingRequest = { id: crypto.randomUUID(), signature };
  }
  const button = form.querySelector('button[type=submit]');
  button.disabled = true;
  showStatus('Salvataggio della richiesta in corso…');
  try {
    const response = await fetch('/api/prelievi', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...data, id: pendingRequest.id })
    });
    const result = await response.json();
    if (!response.ok) {
      if (response.status < 500) pendingRequest = null;
      showStatus(result.error || 'Richiesta non riuscita', 'error');
      return;
    }
    showStatus(`Richiesta ${result.id} salvata. Stato TIBCO: ${result.stato}.`, 'ok');
    lastSavedId = result.id;
    checkStatus.disabled = false;
    pendingRequest = null;
    if (result.stato === 'PRENOTATA') alert('Prelevare il denaro entro 30 secondi');
  } catch {
    showStatus('Connessione interrotta. Riprova: verrà usato lo stesso identificativo.', 'error');
  } finally {
    button.disabled = false;
  }
});

checkStatus.addEventListener('click', async () => {
  if (!lastSavedId) return;
  checkStatus.disabled = true;
  try {
    const response = await fetch(`/api/prelievi/${lastSavedId}`);
    const result = await response.json();
    if (!response.ok) return showStatus(result.error || 'Stato non disponibile', 'error');
    showStatus(`Richiesta ${result.id}: ${result.stato}. ${result.messaggio || ''}`,
      result.stato === 'RIFIUTATA' ? 'error' : 'ok');
  } catch {
    showStatus('Impossibile controllare lo stato: riprova.', 'error');
  } finally {
    checkStatus.disabled = false;
  }
});
