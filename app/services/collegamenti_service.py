"""
services/collegamenti_service.py
Gestione collegamento owner ↔ vet con stati pending/accepted/rejected.
"""
from app.services.supabase_client import get_supabase, get_supabase_admin

STATI = ["pending", "accepted", "rejected"]


def get_tutti_vet() -> list:
    """Restituisce tutti i veterinari registrati sulla piattaforma."""
    supabase = get_supabase()
    result = (
        supabase.table("profiles")
        .select("id, nome, cognome, clinica, telefono, email")
        .eq("ruolo", "vet")
        .order("cognome")
        .execute()
    )
    return result.data or []


def cerca_vet_per_nome(nome: str) -> list:
    """Cerca veterinari registrati per nome/cognome (ricerca fuzzy sul campo nome+cognome)."""
    supabase = get_supabase()
    result = (
        supabase.table("profiles")
        .select("id, nome, cognome, email, clinica")
        .eq("ruolo", "vet")
        .ilike("cognome", f"%{nome}%")
        .execute()
    )
    return result.data or []


def invia_richiesta_collegamento(owner_id: str, vet_id: str) -> bool:
    """L'owner invia una richiesta di collegamento al vet."""
    supabase = get_supabase()
    # Evita duplicati
    existing = (
        supabase.table("collegamenti")
        .select("id, stato")
        .eq("owner_id", owner_id)
        .eq("vet_id", vet_id)
        .execute()
    )
    if existing.data:
        return False  # Già esiste

    result = supabase.table("collegamenti").insert({
        "owner_id": owner_id,
        "vet_id": vet_id,
        "stato": "pending",
    }).execute()
    return bool(result.data)


def get_richieste_vet(vet_id: str) -> list:
    """Restituisce le richieste di collegamento in attesa per il vet."""
    supabase = get_supabase()
    result = (
        supabase.table("collegamenti")
        .select("*, profiles!owner_id(nome, cognome, email)")
        .eq("vet_id", vet_id)
        .eq("stato", "pending")
        .execute()
    )
    return result.data or []


def get_collegamenti_owner(owner_id: str) -> list:
    """Restituisce tutti i collegamenti dell'owner (con stato)."""
    supabase = get_supabase()
    result = (
        supabase.table("collegamenti")
        .select("*, profiles!vet_id(nome, cognome, email, clinica)")
        .eq("owner_id", owner_id)
        .execute()
    )
    return result.data or []


def get_collegamenti_vet(vet_id: str) -> list:
    """Restituisce tutti i proprietari accettati dal vet."""
    supabase = get_supabase()
    result = (
        supabase.table("collegamenti")
        .select("*, profiles!owner_id(nome, cognome, email)")
        .eq("vet_id", vet_id)
        .eq("stato", "accepted")
        .execute()
    )
    return result.data or []


def accetta_collegamento(collegamento_id: str, vet_id: str) -> bool:
    """Il vet accetta la richiesta → aggiorna stato e sincronizza animali."""
    supabase = get_supabase()
    admin = get_supabase_admin()

    # Recupera collegamento
    col = (
        supabase.table("collegamenti")
        .select("*")
        .eq("id", collegamento_id)
        .eq("vet_id", vet_id)
        .single()
        .execute()
    )
    if not col.data:
        return False

    owner_id = col.data["owner_id"]

    # Aggiorna stato collegamento
    supabase.table("collegamenti").update({"stato": "accepted"}).eq("id", collegamento_id).execute()

    # Assegna vet_id agli animali dell'owner (usa admin per bypassare RLS)
    admin.table("animali").update({"vet_id": vet_id}).eq("owner_id", owner_id).is_("vet_id", "null").execute()

    return True


def rifiuta_collegamento(collegamento_id: str, vet_id: str) -> bool:
    supabase = get_supabase()
    result = (
        supabase.table("collegamenti")
        .update({"stato": "rejected"})
        .eq("id", collegamento_id)
        .eq("vet_id", vet_id)
        .execute()
    )
    return bool(result.data)


def invita_vet_via_email(email_vet: str) -> tuple[bool, str]:
    """Invia un invito email a un veterinario non ancora registrato.
    Ritorna (successo, messaggio_errore)."""
    admin = get_supabase_admin()
    try:
        admin.auth.admin.invite_user_by_email(email_vet)
        return True, ""
    except Exception as e:
        return False, str(e)
