-- Eseguire in atm_didattico dopo 01_creazione_tabelle.sql.
-- Funzioni per la demo. Una singola base dati conserva saldo, prenotazioni e storico.

CREATE OR REPLACE FUNCTION public.prenota_prelievo(
    p_id UUID, p_nome TEXT, p_cognome TEXT, p_pin TEXT, p_importo BIGINT
) RETURNS TABLE (esito TEXT, saldo_disponibile_centesimi BIGINT)
LANGUAGE plpgsql AS $$
DECLARE
    v_cliente public.clienti%ROWTYPE;
    v_esistente public.transazioni%ROWTYPE;
    v_disponibile BIGINT;
    v_inserite INTEGER;
BEGIN
    IF p_id IS NULL OR p_importo IS NULL OR p_importo <= 0 THEN
        RETURN QUERY SELECT 'DATI_NON_VALIDI'::TEXT, NULL::BIGINT; RETURN;
    END IF;
    SELECT c.* INTO v_cliente FROM public.clienti c
    WHERE lower(btrim(c.nome)) = lower(btrim(p_nome))
      AND lower(btrim(c.cognome)) = lower(btrim(p_cognome)) AND c.pin = p_pin
    FOR UPDATE;
    IF NOT FOUND THEN
        RETURN QUERY SELECT 'CLIENTE_NON_VALIDO'::TEXT, NULL::BIGINT; RETURN;
    END IF;

    SELECT t.* INTO v_esistente FROM public.transazioni t WHERE t.id_richiesta = p_id FOR UPDATE;
    IF FOUND THEN
        IF v_esistente.cliente_id <> v_cliente.id OR v_esistente.importo_centesimi <> p_importo THEN
            RETURN QUERY SELECT 'CONFLITTO_ID'::TEXT, NULL::BIGINT;
        ELSE
            RETURN QUERY SELECT v_esistente.stato::TEXT,
                (v_cliente.saldo_centesimi - COALESCE((
                    SELECT SUM(t.importo_centesimi) FROM public.transazioni t
                    WHERE t.cliente_id = v_cliente.id AND t.stato = 'PRENOTATA'
                ), 0))::BIGINT;
        END IF;
        RETURN;
    END IF;

    v_disponibile := v_cliente.saldo_centesimi - COALESCE((
        SELECT SUM(t.importo_centesimi) FROM public.transazioni t
        WHERE t.cliente_id = v_cliente.id AND t.stato = 'PRENOTATA'
    ), 0);
    IF p_importo > v_disponibile THEN
        RETURN QUERY SELECT 'SALDO_INSUFFICIENTE'::TEXT, v_disponibile; RETURN;
    END IF;

    INSERT INTO public.transazioni (id_richiesta, cliente_id, importo_centesimi)
    VALUES (p_id, v_cliente.id, p_importo) ON CONFLICT (id_richiesta) DO NOTHING;
    GET DIAGNOSTICS v_inserite = ROW_COUNT;
    IF v_inserite = 0 THEN
        -- Un altro cliente può aver usato contemporaneamente lo stesso UUID.
        RETURN QUERY SELECT 'CONFLITTO_ID'::TEXT, NULL::BIGINT; RETURN;
    END IF;
    RETURN QUERY SELECT 'PRENOTATA'::TEXT, (v_disponibile - p_importo)::BIGINT;
END;
$$;

CREATE OR REPLACE FUNCTION public.concludi_prelievo(
    p_id UUID, p_nome TEXT, p_cognome TEXT, p_pin TEXT, p_importo BIGINT
) RETURNS TABLE (esito TEXT, saldo_centesimi BIGINT)
LANGUAGE plpgsql AS $$
DECLARE
    v_cliente public.clienti%ROWTYPE;
    v_transazione public.transazioni%ROWTYPE;
BEGIN
    SELECT c.* INTO v_cliente FROM public.clienti c
    WHERE lower(btrim(c.nome)) = lower(btrim(p_nome))
      AND lower(btrim(c.cognome)) = lower(btrim(p_cognome)) AND c.pin = p_pin
    FOR UPDATE;
    IF NOT FOUND THEN
        RETURN QUERY SELECT 'CLIENTE_NON_VALIDO'::TEXT, NULL::BIGINT; RETURN;
    END IF;
    SELECT t.* INTO v_transazione FROM public.transazioni t
    WHERE t.id_richiesta = p_id FOR UPDATE;
    IF NOT FOUND THEN
        RETURN QUERY SELECT 'NON_PRENOTATA'::TEXT, v_cliente.saldo_centesimi; RETURN;
    END IF;
    IF v_transazione.cliente_id <> v_cliente.id OR v_transazione.importo_centesimi <> p_importo THEN
        RETURN QUERY SELECT 'CONFLITTO_ID'::TEXT, v_cliente.saldo_centesimi; RETURN;
    END IF;
    IF v_transazione.stato = 'ESEGUITA' THEN
        RETURN QUERY SELECT 'GIA_ELABORATA'::TEXT, v_cliente.saldo_centesimi; RETURN;
    END IF;
    IF v_transazione.stato = 'RIFIUTATA' THEN
        RETURN QUERY SELECT 'RIFIUTATA'::TEXT, v_cliente.saldo_centesimi; RETURN;
    END IF;
    UPDATE public.clienti c SET saldo_centesimi = c.saldo_centesimi - p_importo
    WHERE c.id = v_cliente.id AND c.saldo_centesimi >= p_importo
    RETURNING c.saldo_centesimi INTO v_cliente.saldo_centesimi;
    IF NOT FOUND THEN
        -- Può accadere solo se qualcuno ha modificato il saldo fuori da queste funzioni.
        RETURN QUERY SELECT 'SALDO_INSUFFICIENTE'::TEXT, NULL::BIGINT; RETURN;
    END IF;
    UPDATE public.transazioni t SET stato = 'ESEGUITA', messaggio = 'Prelievo eseguito',
        conclusa_il = CURRENT_TIMESTAMP WHERE t.id_richiesta = p_id;
    RETURN QUERY SELECT 'OK'::TEXT, v_cliente.saldo_centesimi;
END;
$$;

CREATE OR REPLACE FUNCTION public.annulla_prenotazione(p_id UUID, p_motivo TEXT)
RETURNS TEXT LANGUAGE plpgsql AS $$
DECLARE
    v_cliente_id BIGINT;
    v_stato TEXT;
BEGIN
    SELECT t.cliente_id INTO v_cliente_id FROM public.transazioni t WHERE t.id_richiesta = p_id;
    IF NOT FOUND THEN RETURN 'NON_TROVATA'; END IF;
    PERFORM 1 FROM public.clienti c WHERE c.id = v_cliente_id FOR UPDATE;
    SELECT t.stato INTO v_stato FROM public.transazioni t WHERE t.id_richiesta = p_id FOR UPDATE;
    IF v_stato = 'PRENOTATA' THEN
        UPDATE public.transazioni t SET stato = 'RIFIUTATA',
            messaggio = left(coalesce(p_motivo, 'Richiesta annullata'), 200),
            conclusa_il = CURRENT_TIMESTAMP WHERE t.id_richiesta = p_id;
        RETURN 'RIFIUTATA';
    END IF;
    RETURN coalesce(v_stato, 'NON_TROVATA');
END;
$$;
