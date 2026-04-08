# pages/owner/chat.py
# Chat diretta con il veterinario collegato.
import streamlit as st
from app.auth.supabase_auth import get_current_profile
from app.services.collegamenti_service import get_collegamenti_owner
from app.services.messaggi_service import get_conversazione, invia_messaggio, segna_come_letti
from app.components.ui_helpers import format_datetime, empty_state


def show():
    profile = get_current_profile()
    owner_id = profile["id"]

    st.markdown("## 💬 Chat con il veterinario")

    collegamenti = [c for c in get_collegamenti_owner(owner_id) if c.get("stato") == "accepted"]
    if not collegamenti:
        empty_state("💬", "Nessun veterinario collegato", "Collegati a un veterinario per poter chattare.")
        return

    # Selezione vet se ce ne sono più di uno
    nomi_vet = {
        c["vet_id"]: f"🩺 {c['profiles']['nome']} {c['profiles']['cognome']}"
        for c in collegamenti if c.get("profiles")
    }
    if len(nomi_vet) > 1:
        vet_id = st.selectbox("Seleziona veterinario", options=list(nomi_vet.keys()),
                               format_func=lambda x: nomi_vet[x])
    else:
        vet_id = list(nomi_vet.keys())[0]

    # Segna come letti
    segna_come_letti(owner_id, vet_id, owner_id)

    # ── Conversazione ─────────────────────────────────────────────────────────
    messaggi = get_conversazione(owner_id, vet_id)
    _render_chat(messaggi, owner_id)

    # ── Input messaggio ────────────────────────────────────────────────────────
    with st.form("form_chat", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            testo = st.text_input("Scrivi un messaggio…", label_visibility="collapsed")
        with col2:
            sub = st.form_submit_button("Invia ➤", use_container_width=True, type="primary")

    if sub and testo.strip():
        invia_messaggio(owner_id, vet_id, owner_id, testo.strip())
        st.rerun()


def _render_chat(messaggi: list, utente_id: str):
    if not messaggi:
        empty_state("💬", "Nessun messaggio ancora", "Scrivi il primo messaggio al tuo veterinario!")
        return

    for m in messaggi:
        mio = m.get("mittente_id") == utente_id
        align = "flex-end" if mio else "flex-start"
        bg = "#B3A18D" if mio else "#F0F0F0"
        fg = "#fff" if mio else "#3D3028"
        radius = "18px 18px 4px 18px" if mio else "18px 18px 18px 4px"

        st.markdown(
            f"""
            <div style="display:flex; justify-content:{align}; margin-bottom:0.5rem;">
                <div style="max-width:70%; background:{bg}; color:{fg};
                            padding:0.6rem 1rem; border-radius:{radius};
                            font-size:0.95rem; line-height:1.4;">
                    {m.get('testo','')}
                    <div style="font-size:0.7rem; opacity:0.7; margin-top:4px; text-align:right;">
                        {format_datetime(m.get('created_at'))}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
