"""
services/appuntamenti_service.py
Prenotazioni, agenda veterinario, storico visite.
"""
from datetime import date, datetime
from app.services.supabase_client import get_supabase


STATI = ["in_attesa", "confermato", "completato", "annullato"]
STATI_LABEL = {
    "in_attesa": "⏳ In attesa",
    "confermato": "✅ Confermato",
    "completato": "🏁 Completato",
    "annullato": "❌ Annullato",
}


def get_appuntamenti_owner(owner_id: str, futuro: bool = True) -> list:
    supabase = get_supabase()
    oggi = date.today().isoformat()
    query = (
        supabase.table("appuntamenti")
        .select("*, animali!animale_id(nome, specie), profiles!vet_id(nome, cognome)")
        .eq("owner_id", owner_id)
        .neq("stato", "annullato")
        .order("data_ora")
    )
    if futuro:
        query = query.gte("data_ora", oggi)
    return query.execute().data or []


def get_appuntamenti_vet(vet_id: str, data_da: str = None, data_a: str = None) -> list:
    supabase = get_supabase()
    query = (
        supabase.table("appuntamenti")
        .select("*, animali!animale_id(nome, specie), profiles!owner_id(nome, cognome, email)")
        .eq("vet_id", vet_id)
        .order("data_ora")
    )
    if data_da:
        query = query.gte("data_ora", data_da)
    if data_a:
        query = query.lte("data_ora", data_a)
    return query.execute().data or []


def ha_appuntamento_attivo(owner_id: str, vet_id: str, animale_id: str, data_ora: str) -> bool:
    """Restituisce True se esiste già un appuntamento non annullato per stessa combo."""
    supabase = get_supabase()
    result = (
        supabase.table("appuntamenti")
        .select("id")
        .eq("owner_id", owner_id)
        .eq("vet_id", vet_id)
        .eq("animale_id", animale_id)
        .eq("data_ora", data_ora)
        .neq("stato", "annullato")
        .limit(1)
        .execute()
    )
    return bool(result.data)


def crea_appuntamento(data: dict) -> dict | None:
    supabase = get_supabase()
    result = supabase.table("appuntamenti").insert(data).execute()
    return result.data[0] if result.data else None


def aggiorna_stato(appuntamento_id: str, nuovo_stato: str) -> bool:
    if nuovo_stato not in STATI:
        return False
    supabase = get_supabase()
    result = (
        supabase.table("appuntamenti")
        .update({"stato": nuovo_stato})
        .eq("id", appuntamento_id)
        .execute()
    )
    return bool(result.data)


def elimina_appuntamento(appuntamento_id: str) -> bool:
    supabase = get_supabase()
    result = (
        supabase.table("appuntamenti").delete().eq("id", appuntamento_id).execute()
    )
    return bool(result.data)


def get_appuntamenti_oggi(vet_id: str) -> list:
    oggi = date.today().isoformat()
    return get_appuntamenti_vet(vet_id, data_da=oggi + "T00:00:00", data_a=oggi + "T23:59:59")
