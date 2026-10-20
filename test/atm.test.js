const { test } = require('node:test');
const assert = require('node:assert/strict');
const { validateRequest, parseAmount, buildXml } = require('../lib/atm');

const base = { id: '7b6d9f75-5b34-46e7-9d29-7735aa0c567a', nome: 'Mario', cognome: 'Rossi', pin: '12345', importo: '80,00' };

test('conserva PIN con zero iniziale e converte 80 euro in centesimi', () => {
  const result = validateRequest({ ...base, pin: '01234' });
  assert.equal(result.value.pin, '01234');
  assert.equal(result.value.amountCents, 8000);
});

test('accetta apostrofo tipografico e accenti del cliente di esempio', () => {
  const result = validateRequest({ ...base, nome: 'Èlia', cognome: 'D’Amico-Rossi', pin: '01234' });
  assert.equal(result.error, undefined);
  assert.equal(result.value.cognome, 'D’Amico-Rossi');
});

test('rifiuta PIN non valido e importi non positivi o con troppi decimali', () => {
  assert.equal(validateRequest({ ...base, pin: '123' }).error, 'Il PIN deve essere di 5 cifre');
  assert.equal(parseAmount('0'), null);
  assert.equal(parseAmount('-1'), null);
  assert.equal(parseAmount('1.234'), null);
});

test('XML usa l XSD e fa escaping dei nomi', () => {
  const request = validateRequest({ ...base, nome: "D'Èlia", cognome: 'Rossi-Martin' }).value;
  const xml = buildXml(request, new Date('2026-10-20T10:30:00.000Z'));
  assert.match(xml, /<Nome>D&apos;Èlia<\/Nome>/);
  assert.match(xml, /<Importo>80\.00<\/Importo>/);
  assert.match(xml, /<DataOra>2026-10-20T10:30:00\.000Z<\/DataOra>/);
});
