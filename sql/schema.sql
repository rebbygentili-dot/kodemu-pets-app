-- ============================================================
-- Kodemu Pet - Schema SQL Supabase
-- Esegui questo script nell'SQL Editor di Supabase
-- ============================================================

-- Abilita UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── PROFILES ──────────────────────────────────────────────────────────────────
-- Estende auth.users con dati applicativi
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT NOT NULL,
    nome        TEXT NOT NULL,
    cognome     TEXT NOT NULL,
    ruolo       TEXT NOT NULL CHECK (ruolo IN ('owner', 'vet')),
    clinica     TEXT,                        -- solo per vet
    telefono    TEXT,
    avatar_url  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── ANIMALI ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.animali (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id            UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    vet_id              UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    specie              TEXT NOT NULL CHECK (specie IN ('Cane', 'Gatto', 'Cavallo')),
    nome                TEXT NOT NULL,
    razza               TEXT,
    data_nascita        DATE,
    sesso               TEXT CHECK (sesso IN ('Maschio intero', 'Maschio castrato', 'Femmina intera', 'Femmina sterilizzata', 'Non specificato')),
    microchip           TEXT UNIQUE,
    peso_kg             NUMERIC(6,2),
    allergie            TEXT,
    note                TEXT,
    -- Campi gatto
    interno_esterno     TEXT CHECK (interno_esterno IN ('Solo interno', 'Solo esterno', 'Misto')),
    -- Campi cavallo
    passaporto_equino   TEXT,
    scuderia            TEXT,
    foto_url            TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ── CATALOGO VACCINI ──────────────────────────────────────────────────────────
-- Dati di riferimento (popolati da seed_vaccini.sql)
CREATE TABLE IF NOT EXISTS public.vaccini_catalogo (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome        TEXT NOT NULL,
    specie      TEXT NOT NULL CHECK (specie IN ('Cane', 'Gatto', 'Cavallo')),
    tipo        TEXT NOT NULL CHECK (tipo IN ('obbligatorio', 'opzionale')),
    descrizione TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── VACCINAZIONI ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.vaccinazioni (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    animale_id              UUID NOT NULL REFERENCES public.animali(id) ON DELETE CASCADE,
    vaccino_catalogo_id     UUID REFERENCES public.vaccini_catalogo(id) ON DELETE SET NULL,
    nome_vaccino            TEXT NOT NULL,   -- valorizzato dal catalogo o inserito libero
    data_somministrazione   DATE NOT NULL,
    data_prossimo_richiamo  DATE,
    lotto                   TEXT,
    note                    TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ── TERAPIE ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.terapie (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    animale_id  UUID NOT NULL REFERENCES public.animali(id) ON DELETE CASCADE,
    farmaco     TEXT NOT NULL,
    dosaggio    TEXT,
    data_inizio DATE NOT NULL,
    data_fine   DATE,
    attiva      BOOLEAN DEFAULT TRUE,
    note        TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── APPUNTAMENTI ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.appuntamenti (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id    UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    vet_id      UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    animale_id  UUID NOT NULL REFERENCES public.animali(id) ON DELETE CASCADE,
    data_ora    TIMESTAMPTZ NOT NULL,
    motivo      TEXT NOT NULL,
    stato       TEXT NOT NULL DEFAULT 'in_attesa'
                    CHECK (stato IN ('in_attesa', 'confermato', 'completato', 'annullato')),
    note        TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── CARTELLE CLINICHE ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.cartelle_cliniche (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    animale_id              UUID NOT NULL REFERENCES public.animali(id) ON DELETE CASCADE,
    vet_id                  UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    data_visita             TIMESTAMPTZ NOT NULL,
    peso_kg                 NUMERIC(6,2),
    temperatura             NUMERIC(4,1),
    anamnesi                TEXT NOT NULL,
    diagnosi                TEXT NOT NULL,
    terapia_prescritta      TEXT,
    prescrizione_digitale   TEXT,
    note                    TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ── DOCUMENTI ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.documenti (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    animale_id      UUID NOT NULL REFERENCES public.animali(id) ON DELETE CASCADE,
    owner_id        UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    nome_file       TEXT NOT NULL,
    storage_path    TEXT NOT NULL,
    content_type    TEXT,
    tipo            TEXT CHECK (tipo IN ('Referto','Radiografia','Ecografia','Ricetta','Fattura','Vaccinazione','Altro')),
    note            TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── COLLEGAMENTI OWNER ↔ VET ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.collegamenti (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id    UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    vet_id      UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    stato       TEXT NOT NULL DEFAULT 'pending'
                    CHECK (stato IN ('pending', 'accepted', 'rejected')),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (owner_id, vet_id)
);

-- ── LISTINO PREZZI ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.listino_prezzi (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vet_id              UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    nome_prestazione    TEXT NOT NULL,
    categoria           TEXT NOT NULL,
    prezzo              NUMERIC(8,2) NOT NULL DEFAULT 0,
    durata_minuti       INTEGER,
    disponibilita       TEXT DEFAULT 'Entrambi',
    note                TEXT,
    attiva              BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ── RECENSIONI ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.recensioni (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id    UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    vet_id      UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    voto        SMALLINT NOT NULL CHECK (voto BETWEEN 1 AND 5),
    testo       TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (owner_id, vet_id)   -- un owner può recensire lo stesso vet una sola volta
);

-- ── MESSAGGI (CHAT) ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.messaggi (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id        UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    vet_id          UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    mittente_id     UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    testo           TEXT NOT NULL,
    letto           BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================

ALTER TABLE public.vaccini_catalogo  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.animali           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vaccinazioni      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.terapie           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.appuntamenti      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cartelle_cliniche ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documenti         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.collegamenti      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.listino_prezzi    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recensioni         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messaggi          ENABLE ROW LEVEL SECURITY;

-- ── PROFILES
CREATE POLICY "profiles_own" ON public.profiles
    FOR ALL USING (auth.uid() = id);

-- Utenti collegati (accepted) si vedono a vicenda
CREATE POLICY "profiles_readable_by_linked" ON public.profiles
    FOR SELECT USING (
        auth.uid() = id
        OR id IN (
            SELECT owner_id FROM public.collegamenti WHERE vet_id = auth.uid() AND stato = 'accepted'
            UNION
            SELECT vet_id   FROM public.collegamenti WHERE owner_id = auth.uid()
        )
    );

-- Tutti gli utenti autenticati possono cercare veterinari per nome/cognome
CREATE POLICY "profiles_vet_searchable" ON public.profiles
    FOR SELECT USING (ruolo = 'vet' AND auth.uid() IS NOT NULL);

-- Il vet può vedere il profilo degli owner che hanno inviato una richiesta (anche pending)
CREATE POLICY "profiles_owner_readable_by_vet_pending" ON public.profiles
    FOR SELECT USING (
        id IN (
            SELECT owner_id FROM public.collegamenti
            WHERE vet_id = auth.uid()
        )
    );

-- ── ANIMALI
CREATE POLICY "animali_owner_all" ON public.animali
    FOR ALL USING (owner_id = auth.uid());

-- Il vet può leggere gli animali degli owner con collegamento accepted
CREATE POLICY "animali_vet_linked_read" ON public.animali
    FOR SELECT USING (
        owner_id IN (
            SELECT owner_id FROM public.collegamenti
            WHERE vet_id = auth.uid() AND stato = 'accepted'
        )
    );

-- ── CATALOGO VACCINI
-- Lettura per tutti gli utenti autenticati (dati di riferimento)
CREATE POLICY "catalogo_vaccini_read" ON public.vaccini_catalogo
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- ── VACCINAZIONI
-- Owner: lettura propri animali
CREATE POLICY "vaccinazioni_owner_read" ON public.vaccinazioni
    FOR SELECT USING (
        animale_id IN (SELECT id FROM public.animali WHERE owner_id = auth.uid())
    );
-- Owner: inserimento vaccini sui propri animali
CREATE POLICY "vaccinazioni_owner_insert" ON public.vaccinazioni
    FOR INSERT WITH CHECK (
        animale_id IN (SELECT id FROM public.animali WHERE owner_id = auth.uid())
    );
-- Owner: aggiornamento vaccini sui propri animali
CREATE POLICY "vaccinazioni_owner_update" ON public.vaccinazioni
    FOR UPDATE USING (
        animale_id IN (SELECT id FROM public.animali WHERE owner_id = auth.uid())
    );
-- Vet: gestione completa (basato su collegamento accettato)
CREATE POLICY "vaccinazioni_vet_all" ON public.vaccinazioni
    FOR ALL USING (
        animale_id IN (
            SELECT a.id FROM public.animali a
            INNER JOIN public.collegamenti c ON c.owner_id = a.owner_id
            WHERE c.vet_id = auth.uid() AND c.stato = 'accepted'
        )
    );

-- ── TERAPIE
CREATE POLICY "terapie_owner_read" ON public.terapie
    FOR SELECT USING (
        animale_id IN (SELECT id FROM public.animali WHERE owner_id = auth.uid())
    );
CREATE POLICY "terapie_vet_all" ON public.terapie
    FOR ALL USING (
        animale_id IN (
            SELECT a.id FROM public.animali a
            INNER JOIN public.collegamenti c ON c.owner_id = a.owner_id
            WHERE c.vet_id = auth.uid() AND c.stato = 'accepted'
        )
    );

-- ── APPUNTAMENTI
CREATE POLICY "appuntamenti_owner" ON public.appuntamenti
    FOR ALL USING (owner_id = auth.uid());

CREATE POLICY "appuntamenti_vet" ON public.appuntamenti
    FOR ALL USING (vet_id = auth.uid());

-- ── CARTELLE CLINICHE
CREATE POLICY "cartelle_vet_all" ON public.cartelle_cliniche
    FOR ALL USING (vet_id = auth.uid());

CREATE POLICY "cartelle_owner_read" ON public.cartelle_cliniche
    FOR SELECT USING (
        animale_id IN (SELECT id FROM public.animali WHERE owner_id = auth.uid())
    );

-- ── DOCUMENTI
CREATE POLICY "documenti_owner_read" ON public.documenti
    FOR SELECT USING (owner_id = auth.uid());
CREATE POLICY "documenti_vet_all" ON public.documenti
    FOR ALL USING (
        animale_id IN (
            SELECT a.id FROM public.animali a
            INNER JOIN public.collegamenti c ON c.owner_id = a.owner_id
            WHERE c.vet_id = auth.uid() AND c.stato = 'accepted'
        )
    );

-- ── COLLEGAMENTI
CREATE POLICY "collegamenti_owner" ON public.collegamenti
    FOR ALL USING (owner_id = auth.uid());

CREATE POLICY "collegamenti_vet" ON public.collegamenti
    FOR ALL USING (vet_id = auth.uid());

-- ── LISTINO PREZZI
CREATE POLICY "listino_vet_all" ON public.listino_prezzi
    FOR ALL USING (vet_id = auth.uid());

CREATE POLICY "listino_owner_read" ON public.listino_prezzi
    FOR SELECT USING (
        vet_id IN (
            SELECT vet_id FROM public.collegamenti
            WHERE owner_id = auth.uid() AND stato = 'accepted'
        )
    );

-- ── RECENSIONI
-- Tutti gli utenti autenticati possono leggere le recensioni
CREATE POLICY "recensioni_read" ON public.recensioni
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- Solo owner con collegamento accepted possono inserire una recensione
CREATE POLICY "recensioni_owner_insert" ON public.recensioni
    FOR INSERT WITH CHECK (
        owner_id = auth.uid()
        AND vet_id IN (
            SELECT vet_id FROM public.collegamenti
            WHERE owner_id = auth.uid() AND stato = 'accepted'
        )
    );

-- L'owner può modificare/eliminare solo le proprie recensioni
CREATE POLICY "recensioni_owner_update" ON public.recensioni
    FOR UPDATE USING (owner_id = auth.uid());

CREATE POLICY "recensioni_owner_delete" ON public.recensioni
    FOR DELETE USING (owner_id = auth.uid());

-- ── MESSAGGI
CREATE POLICY "messaggi_partecipanti" ON public.messaggi
    FOR ALL USING (owner_id = auth.uid() OR vet_id = auth.uid());

-- ============================================================
-- TRIGGER: updated_at automatico
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_profiles_updated_at ON public.profiles;
CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS trg_animali_updated_at ON public.animali;
CREATE TRIGGER trg_animali_updated_at
    BEFORE UPDATE ON public.animali
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS trg_listino_updated_at ON public.listino_prezzi;
CREATE TRIGGER trg_listino_updated_at
    BEFORE UPDATE ON public.listino_prezzi
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- TRIGGER: nuovo utente → crea profilo automaticamente
-- ============================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, nome, cognome, ruolo)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'nome', ''),
        COALESCE(NEW.raw_user_meta_data->>'cognome', ''),
        COALESCE(NEW.raw_user_meta_data->>'ruolo', 'owner')
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- STORAGE BUCKET
-- ============================================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('documenti-animali', 'documenti-animali', false)
ON CONFLICT (id) DO NOTHING;

-- Policy storage: utenti autenticati possono caricare, leggere ed eliminare
-- i propri documenti nel bucket documenti-animali
CREATE POLICY "owner_upload" ON storage.objects
    FOR INSERT TO authenticated
    WITH CHECK (bucket_id = 'documenti-animali');

CREATE POLICY "owner_select" ON storage.objects
    FOR SELECT TO authenticated
    USING (bucket_id = 'documenti-animali');

CREATE POLICY "owner_delete" ON storage.objects
    FOR DELETE TO authenticated
    USING (bucket_id = 'documenti-animali');

-- ============================================================
-- INDICI per performance
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_animali_owner   ON public.animali(owner_id);
CREATE INDEX IF NOT EXISTS idx_animali_vet     ON public.animali(vet_id);
CREATE INDEX IF NOT EXISTS idx_vaccinazioni_animale  ON public.vaccinazioni(animale_id);
CREATE INDEX IF NOT EXISTS idx_catalogo_specie       ON public.vaccini_catalogo(specie);
CREATE INDEX IF NOT EXISTS idx_terapie_animale ON public.terapie(animale_id);
CREATE INDEX IF NOT EXISTS idx_appuntamenti_owner ON public.appuntamenti(owner_id);
CREATE INDEX IF NOT EXISTS idx_appuntamenti_vet   ON public.appuntamenti(vet_id);
CREATE INDEX IF NOT EXISTS idx_appuntamenti_data  ON public.appuntamenti(data_ora);
CREATE INDEX IF NOT EXISTS idx_cartelle_animale   ON public.cartelle_cliniche(animale_id);
CREATE INDEX IF NOT EXISTS idx_messaggi_conv      ON public.messaggi(owner_id, vet_id);
CREATE INDEX IF NOT EXISTS idx_recensioni_vet     ON public.recensioni(vet_id);
CREATE INDEX IF NOT EXISTS idx_collegamenti_owner ON public.collegamenti(owner_id);
CREATE INDEX IF NOT EXISTS idx_collegamenti_vet   ON public.collegamenti(vet_id);
