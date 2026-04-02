"""
services/supabase_client.py
Connessione centralizzata a Supabase.
"""
import streamlit as st
from supabase import create_client, Client


def get_supabase() -> Client:
    """Client Supabase autenticato con il JWT dell'utente corrente (database + storage)."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    client = create_client(url, key)
    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")
    if access_token and refresh_token:
        client.auth.set_session(access_token, refresh_token)
    elif access_token:
        client.postgrest.auth(access_token)
    return client


@st.cache_resource
def get_supabase_admin() -> Client:
    """Client con service_role_key per operazioni admin (es. inviti email)."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["service_role_key"]
    return create_client(url, key)
