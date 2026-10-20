require('dotenv').config();
const express = require('express');
const { Pool } = require('pg');
const path = require('node:path');
const fs = require('node:fs/promises');
const { randomUUID } = require('node:crypto');
const { validateRequest, buildXml, UUID_PATTERN } = require('./lib/atm');

const app = express();
const pool = new Pool({
  host: process.env.ATM_DB_HOST || 'localhost',
  port: Number(process.env.ATM_DB_PORT || 5432),
  database: process.env.ATM_DB_NAME || 'atm_didattico',
  user: process.env.ATM_DB_USER || 'postgres',
  password: process.env.ATM_DB_PASSWORD,
  max: 5
});
const outputDir = path.resolve(process.env.ATM_OUTPUT_DIR || path.join(__dirname, 'input'));
const host = process.env.ATM_HOST || '127.0.0.1';
const port = Number(process.env.ATM_PORT || 3000);
const activeIds = new Set();

app.use(express.json({ limit: '16kb' }));
app.use(express.static(path.join(__dirname, 'public')));

app.post('/api/prelievi', async (req, res) => {
  const checked = validateRequest(req.body);
  if (checked.error) return res.status(400).json({ error: checked.error });
  const data = checked.value;
  if (activeIds.has(data.id)) return res.status(409).json({ error: 'Richiesta già in corso: riprova tra poco' });
  activeIds.add(data.id);
  let reserved = false;
  try {
    const result = await pool.query(
      'SELECT esito, saldo_disponibile_centesimi FROM public.prenota_prelievo($1::uuid,$2,$3,$4,$5::bigint)',
      [data.id, data.nome, data.cognome, data.pin, data.amountCents]
    );
    const esito = result.rows[0]?.esito;
    if (esito === 'CLIENTE_NON_VALIDO') return res.status(403).json({ error: 'Cliente o PIN non riconosciuti' });
    if (esito === 'SALDO_INSUFFICIENTE') return res.status(409).json({ error: 'Saldo insufficiente' });
    if (esito === 'CONFLITTO_ID') return res.status(409).json({ error: 'Identificativo già usato per un’altra richiesta' });
    if (esito === 'RIFIUTATA') return res.status(409).json({ error: 'Richiesta già rifiutata' });
    if (esito === 'ESEGUITA') return res.json({ id: data.id, stato: 'ESEGUITA' });
    if (esito !== 'PRENOTATA') return res.status(400).json({ error: 'Dati non validi' });
    reserved = true;

    await fs.mkdir(outputDir, { recursive: true });
    const target = path.join(outputDir, `${data.id}.xml`);
    try {
      await fs.access(target);
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
      const temporary = path.join(outputDir, `${data.id}.${randomUUID()}.tmp`);
      try {
        await fs.writeFile(temporary, buildXml(data), { encoding: 'utf8', flag: 'wx' });
        await fs.rename(temporary, target);
      } finally {
        await fs.rm(temporary, { force: true }).catch(() => {});
      }
    }
    return res.status(201).json({ id: data.id, stato: 'PRENOTATA' });
  } catch (error) {
    console.error('Errore nella richiesta ATM:', error.message);
    if (reserved) {
      // La richiesta rimane prenotata: un retry con lo stesso ID riprova la scrittura.
      return res.status(503).json({ error: 'XML non salvato. Riprova con la stessa richiesta.' });
    }
    return res.status(503).json({ error: 'PostgreSQL non disponibile. Riprova più tardi.' });
  } finally {
    activeIds.delete(data.id);
  }
});

app.get('/api/prelievi/:id', async (req, res) => {
  if (!UUID_PATTERN.test(req.params.id)) return res.status(400).json({ error: 'ID non valido' });
  try {
    const result = await pool.query(
      'SELECT stato, messaggio FROM public.transazioni WHERE id_richiesta = $1::uuid', [req.params.id]
    );
    if (!result.rowCount) return res.status(404).json({ error: 'Richiesta non trovata' });
    return res.json({ id: req.params.id, ...result.rows[0] });
  } catch {
    return res.status(503).json({ error: 'PostgreSQL non disponibile' });
  }
});

app.listen(port, host, () => console.log(`ATM demo: http://${host}:${port}`));
