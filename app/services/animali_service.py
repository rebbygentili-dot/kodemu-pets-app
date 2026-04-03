"""
services/animali_service.py
CRUD animali + logica specie-specifica.
"""
from app.services.supabase_client import get_supabase

SPECIE = ["Cane", "Gatto", "Cavallo"]

VACCINI_CONSIGLIATI = {
    "Cane": ["Morbo di Carré", "Parvovirus", "Epatite", "Leptospirosi", "Rabbia"],
    "Gatto": ["Trivalente (Rinotracheite, Calicivirus, Panleucopenia)", "FeLV"],
    "Cavallo": ["Influenza equina", "Tetano"],
}

SUGGERIMENTI = {
    "Cane": [
        "Ricorda la profilassi filaria ogni 30 giorni.",
        "Programma il vaccino annuale polivalente.",
        "Antiparassitario (zecche/pulci) ogni mese nella bella stagione.",
    ],
    "Gatto": [
        "Se è un gatto che esce, valuta l'antiparassitario mensile.",
        "Promemoria: richiamo vaccino trivalente ogni 12 mesi.",
        "Test FIV/FeLV consigliato se il gatto ha accesso all'esterno.",
    ],
    "Cavallo": [
        "Ricorda di programmare il vermifugo ogni 3 mesi.",
        "Il cavallo richiede ferratura ogni 30–45 giorni.",
        "Richiamo vaccino influenza/tetano annuale.",
        "Visita dentistica ogni 6-12 mesi.",
    ],
}


def get_animali_by_owner(owner_id: str) -> list:
    supabase = get_supabase()
    result = (
        supabase.table("animali")
        .select("*")
        .eq("owner_id", owner_id)
        .order("nome")
        .execute()
    )
    return result.data or []


def get_animali_by_vet(vet_id: str) -> list:
    """Restituisce tutti gli animali dei proprietari collegati al vet (stato accepted)."""
    supabase = get_supabase()
    collegamenti = (
        supabase.table("collegamenti")
        .select("owner_id")
        .eq("vet_id", vet_id)
        .eq("stato", "accepted")
        .execute()
    )
    owner_ids = [c["owner_id"] for c in (collegamenti.data or [])]
    if not owner_ids:
        return []
    result = (
        supabase.table("animali")
        .select("*, profiles!owner_id(nome, cognome, email)")
        .in_("owner_id", owner_ids)
        .order("nome")
        .execute()
    )
    return result.data or []


def get_animale_by_id(animale_id: str) -> dict | None:
    supabase = get_supabase()
    result = (
        supabase.table("animali").select("*").eq("id", animale_id).single().execute()
    )
    return result.data


def crea_animale(data: dict) -> dict | None:
    import streamlit as st
    supabase = get_supabase()
    try:
        result = supabase.table("animali").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        st.error(f"Errore dettagliato: {e}")
        return None


def aggiorna_animale(animale_id: str, data: dict) -> bool:
    supabase = get_supabase()
    result = supabase.table("animali").update(data).eq("id", animale_id).execute()
    return bool(result.data)


def elimina_animale(animale_id: str) -> bool:
    supabase = get_supabase()
    result = supabase.table("animali").delete().eq("id", animale_id).execute()
    return bool(result.data)


def get_suggerimenti(specie: str) -> list[str]:
    return SUGGERIMENTI.get(specie, [])


def get_vaccini_consigliati(specie: str) -> list[str]:
    return VACCINI_CONSIGLIATI.get(specie, [])
