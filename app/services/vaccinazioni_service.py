"""
services/vaccinazioni_service.py
Gestione libretto vaccinale e terapie.
"""
from datetime import date
from app.services.supabase_client import get_supabase


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


def aggiorna_vaccinazione(vaccino_id: str, data: dict) -> bool:
    supabase = get_supabase()
    result = (
        supabase.table("vaccinazioni").update(data).eq("id", vaccino_id).execute()
    )
    return bool(result.data)


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
