// Live checks that must not create a reservation or an XML file.
// Run only while the local ATM demo and PostgreSQL are available.
require('dotenv').config();
const assert = require('node:assert/strict');
const { randomUUID } = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.ATM_DB_HOST || 'localhost',
  port: Number(process.env.ATM_DB_PORT || 5432),
  database: process.env.ATM_DB_NAME || 'atm_didattico',
  user: process.env.ATM_DB_USER || 'postgres',
  password: process.env.ATM_DB_PASSWORD,
  connectionTimeoutMillis: 3000
});
const input = path.resolve(process.env.ATM_OUTPUT_DIR || path.join(__dirname, '..', 'input'));
const endpoint = `http://${process.env.ATM_HOST || '127.0.0.1'}:${process.env.ATM_PORT || 3000}/api/prelievi`;

async function snapshot() {
  const { rows } = await pool.query(`
    SELECT (SELECT count(*) FROM public.transazioni) AS transazioni,
           (SELECT coalesce(sum(saldo_centesimi),0) FROM public.clienti) AS saldo
  `);
  return {
    ...rows[0],
    files: fs.readdirSync(input).filter(name => name.endsWith('.xml')).sort()
  };
}

async function check(label, changes, status, message) {
  const body = {
    id: randomUUID(), nome: 'Mario', cognome: 'Rossi', pin: '12345', importo: '50',
    ...changes
  };
  const response = await fetch(endpoint, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const result = await response.json();
  assert.equal(response.status, status, `${label}: HTTP ${response.status}`);
  assert.equal(result.error, message, `${label}: ${JSON.stringify(result)}`);
  console.log(`OK ${label}: HTTP ${status}`);
}

(async () => {
  const before = await snapshot();
  const cases = [
    ['TC_02 PIN corto', { pin: '123' }, 400, 'Il PIN deve essere di 5 cifre'],
    ['TC_06 nome vuoto', { nome: '' }, 400, 'Inserisci nome e cognome validi'],
    ['TC_06 cognome vuoto', { cognome: '' }, 400, 'Inserisci nome e cognome validi'],
    ['TC_06 solo spazi', { nome: '   ' }, 400, 'Inserisci nome e cognome validi'],
    ['TC_07 PIN con lettera', { pin: '12a45' }, 400, 'Il PIN deve essere di 5 cifre'],
    ['TC_07 PIN lungo', { pin: '123456' }, 400, 'Il PIN deve essere di 5 cifre'],
    ['TC_08 PIN errato', { pin: '54321' }, 403, 'Cliente o PIN non riconosciuti'],
    ['TC_08 nome ignoto', { nome: 'Sconosciuto' }, 403, 'Cliente o PIN non riconosciuti']
  ];
  for (const value of ['', '0', '-10', 'abc', 'NaN', 'Infinity', '1e2', '10.001']) {
    cases.push([`TC_10 importo ${JSON.stringify(value)}`,
      { importo: value }, 400, 'Inserisci un importo positivo con al massimo due decimali']);
  }
  for (const args of cases) await check(...args);
  const after = await snapshot();
  assert.deepEqual(after, before, 'Una richiesta rifiutata ha modificato database o input');
  console.log(`OK: ${cases.length} rifiuti, database e input invariati`);
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
}).finally(() => pool.end());
