const NAME_PATTERN = /^[\p{L}][\p{L}\p{M} .'’\-]*$/u;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function parseAmount(value) {
  const normalized = String(value ?? '').trim().replace(',', '.');
  if (!/^(?:0|[1-9]\d*)(?:\.\d{1,2})?$/.test(normalized)) return null;
  const [euros, cents = ''] = normalized.split('.');
  const amount = Number(euros) * 100 + Number(cents.padEnd(2, '0'));
  return Number.isSafeInteger(amount) && amount > 0 ? amount : null;
}

function validateRequest(body) {
  const nome = String(body?.nome ?? '').trim();
  const cognome = String(body?.cognome ?? '').trim();
  const pin = String(body?.pin ?? '');
  const id = String(body?.id ?? '');
  const amountCents = parseAmount(body?.importo);
  if (!UUID_PATTERN.test(id)) return { error: 'Identificativo richiesta non valido' };
  if (!nome || !cognome || nome.length > 100 || cognome.length > 100 ||
      !NAME_PATTERN.test(nome) || !NAME_PATTERN.test(cognome)) {
    return { error: 'Inserisci nome e cognome validi' };
  }
  if (!/^[0-9]{5}$/.test(pin)) return { error: 'Il PIN deve essere di 5 cifre' };
  if (amountCents === null) return { error: 'Inserisci un importo positivo con al massimo due decimali' };
  return { value: { id, nome, cognome, pin, amountCents } };
}

function escapeXml(value) {
  return String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&apos;');
}

function buildXml(request, timestamp = new Date()) {
  const euro = (request.amountCents / 100).toFixed(2);
  return `<?xml version="1.0" encoding="UTF-8"?>\n<TransazioneATM>\n  <Cliente>\n    <Nome>${escapeXml(request.nome)}</Nome>\n    <Cognome>${escapeXml(request.cognome)}</Cognome>\n    <PIN>${request.pin}</PIN>\n  </Cliente>\n  <DettagliPrelievo>\n    <Importo>${euro}</Importo>\n    <DataOra>${timestamp.toISOString()}</DataOra>\n  </DettagliPrelievo>\n</TransazioneATM>\n`;
}

module.exports = { parseAmount, validateRequest, buildXml, UUID_PATTERN };
