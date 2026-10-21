-- Progetto ATM: eseguire tutto nel Query Tool del database atm_didattico.
-- Solo dati fittizi. Questo script prepara le tabelle, non esegue prelievi.
-- Ripeterlo non modifica i saldi dei clienti gia' presenti.

BEGIN;

DO $$
BEGIN
    IF current_database() <> 'atm_didattico' THEN
        RAISE EXCEPTION 'Apri il Query Tool sul database atm_didattico.';
    END IF;
END;
$$;

CREATE TABLE IF NOT EXISTS public.clienti (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(100) NOT NULL CHECK (length(btrim(nome)) > 0),
    cognome VARCHAR(100) NOT NULL CHECK (length(btrim(cognome)) > 0),
    -- Testuale per conservare anche PIN come 01234. Previsto dalla traccia del progetto.
    pin VARCHAR(5) NOT NULL UNIQUE CHECK (pin ~ '^[0-9]{5}$'),
    -- Saldo contabile: le prenotazioni saranno sottratte per la disponibilita'.
    saldo_centesimi BIGINT NOT NULL CHECK (saldo_centesimi >= 0)
);

CREATE TABLE IF NOT EXISTS public.transazioni (
    -- Lo stesso ID dovra' essere usato da pagina, XML e retry.
    id_richiesta UUID PRIMARY KEY,
    cliente_id BIGINT NOT NULL REFERENCES public.clienti(id),
    importo_centesimi BIGINT NOT NULL CHECK (importo_centesimi > 0),
    stato VARCHAR(20) NOT NULL DEFAULT 'PRENOTATA'
        CHECK (stato IN ('PRENOTATA', 'ESEGUITA', 'RIFIUTATA')),
    messaggio TEXT,
    creata_il TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    conclusa_il TIMESTAMPTZ,
    CHECK (
        (stato = 'PRENOTATA' AND conclusa_il IS NULL)
        OR
        (stato IN ('ESEGUITA', 'RIFIUTATA') AND conclusa_il IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS transazioni_cliente_stato_idx
    ON public.transazioni (cliente_id, stato);

COMMIT;

-- Verifica finale: non mostriamo il PIN nel risultato.
SELECT
    id,
    nome,
    cognome,
    saldo_centesimi,
    (saldo_centesimi / 100.0)::NUMERIC(18, 2) AS saldo_euro
FROM public.clienti
ORDER BY id;

