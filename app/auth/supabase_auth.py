"""
auth/supabase_auth.py
Gestione autenticazione: registrazione, login, logout, sessione.
"""
import streamlit as st
from app.services.supabase_client import get_supabase


def login(email: str, password: str) -> dict | None:
    """
    Esegue il login con email e password.
    Ritorna il dato utente o None in caso di errore.
    """
    supabase = get_supabase()
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        user = response.user
        session = response.session
        if user and session:
            st.session_state["user"] = user
            st.session_state["access_token"] = session.access_token
            st.session_state["refresh_token"] = session.refresh_token
            # Carica il profilo (ruolo, nome, ecc.)
            profile = _load_profile(user.id)
            st.session_state["profile"] = profile
            return user
    except Exception as e:
        st.error(f"Errore login: {e}")
    return None


def register(email: str, password: str, nome: str, cognome: str, ruolo: str) -> bool:
    """
    Registra un nuovo utente (owner o vet).
    Crea l'utente in Supabase Auth e inserisce il profilo nella tabella profiles.
    """
    supabase = get_supabase()
    try:
        response = supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "nome": nome,
                        "cognome": cognome,
                        "ruolo": ruolo,
                    }
                },
            }
        )
        user = response.user
        if user:
            # Il profilo viene creato automaticamente dal trigger handle_new_user
            return True
    except Exception:
        pass
    return False


def completa_profilo(user_id: str, nome: str, cognome: str, ruolo: str, clinica: str | None = None) -> bool:
    """Aggiorna il profilo di un utente invitato che non ha ancora completato la registrazione."""
    supabase = get_supabase()
    try:
        supabase.table("profiles").update({
            "nome": nome,
            "cognome": cognome,
            "ruolo": ruolo,
            "clinica": clinica or None,
        }).eq("id", user_id).execute()
        # Ricarica il profilo in sessione
        profile = _load_profile(user_id)
        st.session_state["profile"] = profile
        return True
    except Exception:
        return False


def logout():
    """Esegue il logout e pulisce la sessione Streamlit."""
    supabase = get_supabase()
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    for key in ["user", "access_token", "refresh_token", "profile"]:
        st.session_state.pop(key, None)


def get_current_user() -> dict | None:
    """Restituisce l'utente corrente dalla sessione."""
    return st.session_state.get("user")


def get_current_profile() -> dict | None:
    """Restituisce il profilo (con ruolo) dell'utente corrente."""
    return st.session_state.get("profile")


def is_logged_in() -> bool:
    return "user" in st.session_state and st.session_state["user"] is not None


def get_ruolo() -> str | None:
    """Ritorna 'owner' o 'vet' in base al profilo loggato."""
    profile = get_current_profile()
    if profile:
        return profile.get("ruolo")
    return None


def _load_profile(user_id: str) -> dict | None:
    supabase = get_supabase()
    try:
        result = (
            supabase.table("profiles")
            .select("*")
            .eq("id", user_id)
            .single()
            .execute()
        )
        return result.data
    except Exception:
        return None
