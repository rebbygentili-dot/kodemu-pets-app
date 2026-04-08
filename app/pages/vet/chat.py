# pages/vet/chat.py
# Chat con i proprietari collegati, lato veterinario.
import streamlit as st
from app.auth.supabase_auth import get_current_profile
from app.services.collegamenti_service import get_collegamenti_vet
from app.services.messaggi_service import get_conversazione, invia_messaggio, segna_come_letti
from app.components.ui_helpers import format_datetime, empty_state


def show():
    profile = get_current_profile()
    vet_id = profile["id"]

    st.markdown("## 💬 Chat con i proprietari")

    proprietari = get_collegamenti_vet(vet_id)
    if not proprietari:
        empty_state("💬", "Nessun proprietario collegato")
        return

    nomi = {
        c["owner_id"]: f"👤 {c['profiles']['nome']} {c['profiles']['cognome']}"
        for c in proprietari if c.get("profiles")
    }
    owner_id = st.selectbox("Seleziona proprietario", options=list(nomi.keys()),
                             format_func=lambda x: nomi[x])

    segna_come_letti(owner_id, vet_id, vet_id)

    messaggi = get_conversazione(owner_id, vet_id)
    _render_chat(messaggi, vet_id)

    with st.form("form_chat_vet", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            testo = st.text_input("Scrivi un messaggio…", label_visibility="collapsed")
        with col2:
            sub = st.form_submit_button("Invia ➤", use_container_width=True, type="primary")

    if sub and testo.strip():
        invia_messaggio(owner_id, vet_id, vet_id, testo.strip())
        st.rerun()


def _render_chat(messaggi: list, utente_id: str):
    if not messaggi:
        empty_state("💬", "Nessun messaggio ancora")
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
                            padding:0.6rem 1rem; border-radius:{radius}; font-size:0.95rem; line-height:1.4;">
                    {m.get('testo','')}
                    <div style="font-size:0.7rem; opacity:0.7; margin-top:4px; text-align:right;">
                        {format_datetime(m.get('created_at'))}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
