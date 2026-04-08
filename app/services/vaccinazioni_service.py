# services/vaccinazioni_service.py
# Libretto vaccinale e terapie dell'animale. Il catalogo vaccini viene da vaccini_catalogo.
from datetime import date
from app.services.supabase_client import get_supabase


# ── Catalogo vaccini ──────────────────────────────────────────────────────────

def get_catalogo_vaccini(specie: str) -> list:
    # Legge da vaccini_catalogo — obbligatori prima, opzionali dopo
    supabase = get_supabase()
    result = (
        supabase.table("vaccini_catalogo")
        .select("id, nome, tipo, descrizione")
        .eq("specie", specie)
        .order("tipo")
        .order("nome")
        .execute()
    )
    return result.data or []


# ── Vaccinazioni ──────────────────────────────────────────────────────────────

def get_vaccinazioni(animale_id: str) -> list:
    supabase = get_supabase()
    result = (
        supabase.table("vaccinazioni")
        .select("*")
        .eq("animale_id", animale_id)
        .order("data_somministrazione", desc=True)
        .execute()
    )
    return result.data or []


def aggiungi_vaccinazione(data: dict) -> dict | None:
    supabase = get_supabase()
    result = supabase.table("vaccinazioni").insert(data).execute()
    return result.data[0] if result.data else None


def elimina_vaccinazione(vaccino_id: str) -> bool:
    supabase = get_supabase()
    result = supabase.table("vaccinazioni").delete().eq("id", vaccino_id).execute()
    return bool(result.data)


def get_vaccinazioni_in_scadenza(owner_id: str, giorni: int = 30) -> list:
    """Restituisce vaccini in scadenza nei prossimi N giorni per tutti gli animali dell'owner."""
    from datetime import timedelta
    supabase = get_supabase()

    # Prima prendi gli animali dell'owner
    animali_result = (
        supabase.table("animali")
        .select("id, nome, specie")
        .eq("owner_id", owner_id)
        .execute()
    )
    animali = animali_result.data or []
    if not animali:
        return []

    animali_ids = [a["id"] for a in animali]
    animali_map = {a["id"]: a for a in animali}

    oggi = date.today()
    fra_n_giorni = (oggi + timedelta(days=giorni)).isoformat()

    result = (
        supabase.table("vaccinazioni")
        .select("*")
        .in_("animale_id", animali_ids)
        .not_.is_("data_prossimo_richiamo", "null")
        .lte("data_prossimo_richiamo", fra_n_giorni)
        .gte("data_prossimo_richiamo", oggi.isoformat())
        .execute()
    )

    vaccinazioni = result.data or []
    for v in vaccinazioni:
        animale = animali_map.get(v["animale_id"], {})
        v["animale_nome"] = animale.get("nome", "")
        v["animale_specie"] = animale.get("specie", "")

    return vaccinazioni


# ── Terapie ───────────────────────────────────────────────────────────────────

def get_terapie(animale_id: str, solo_attive: bool = False) -> list:
    supabase = get_supabase()
    query = (
        supabase.table("terapie")
        .select("*")
        .eq("animale_id", animale_id)
        .order("data_inizio", desc=True)
    )
    if solo_attive:
        query = query.eq("attiva", True)
    return query.execute().data or []


def aggiungi_terapia(data: dict) -> dict | None:
    supabase = get_supabase()
    result = supabase.table("terapie").insert(data).execute()
    return result.data[0] if result.data else None


def aggiorna_terapia(terapia_id: str, data: dict) -> bool:
    supabase = get_supabase()
    result = supabase.table("terapie").update(data).eq("id", terapia_id).execute()
    return bool(result.data)


def termina_terapia(terapia_id: str) -> bool:
    return aggiorna_terapia(terapia_id, {"attiva": False, "data_fine": date.today().isoformat()})


def elimina_terapia(terapia_id: str) -> bool:
    supabase = get_supabase()
    result = supabase.table("terapie").delete().eq("id", terapia_id).execute()
    return bool(result.data)


# ── Integratori (cavalli) ─────────────────────────────────────────────────────

INTEGRATORI_CATALOGO = ["Elettroliti", "Olio di semi di lino", "Biotina", "Altro"]


def get_integratori(animale_id: str) -> list:
    supabase = get_supabase()
    return (
        supabase.table("terapie")
        .select("*")
        .eq("animale_id", animale_id)
        .eq("categoria", "integratore")
        .order("data_inizio", desc=True)
        .execute()
        .data or []
    )


def aggiungi_integratore(data: dict) -> dict | None:
    supabase = get_supabase()
    payload = {**data, "categoria": "integratore"}
    result = supabase.table("terapie").insert(payload).execute()
    return result.data[0] if result.data else None


def elimina_integratore(integratore_id: str) -> bool:
    supabase = get_supabase()
    result = supabase.table("terapie").delete().eq("id", integratore_id).execute()
    return bool(result.data)


# ── Antiparassitari (cani e gatti) ───────────────────────────────────────────

TIPI_SOMMINISTRAZIONE = ["Pipetta", "Pastiglia", "Spray", "Collare"]
COPERTURE_ANTIPARASSITARIO = ["Pulci", "Zecche", "Pappataci", "Pulci + Zecche", "Tutto (pulci, zecche, pappataci)"]


def get_antiparassitari(animale_id: str) -> list:
    supabase = get_supabase()
    return (
        supabase.table("terapie")
        .select("*")
        .eq("animale_id", animale_id)
        .eq("categoria", "antiparassitario")
        .order("data_inizio", desc=True)
        .execute()
        .data or []
    )


def aggiungi_antiparassitario(data: dict) -> dict | None:
    supabase = get_supabase()
    payload = {**data, "categoria": "antiparassitario"}
    result = supabase.table("terapie").insert(payload).execute()
    return result.data[0] if result.data else None


def elimina_antiparassitario(antiparassitario_id: str) -> bool:
    supabase = get_supabase()
    result = supabase.table("terapie").delete().eq("id", antiparassitario_id).execute()
    return bool(result.data)
