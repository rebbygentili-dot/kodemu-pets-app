"""
pages/owner/appuntamenti.py
Appuntamenti del proprietario: accetta/rifiuta proposte del veterinario.
"""
import streamlit as st
from app.auth.supabase_auth import get_current_profile
from app.services.appuntamenti_service import (
    get_appuntamenti_owner, aggiorna_stato, STATI_LABEL,
)
from app.components.ui_helpers import format_datetime, render_badge, empty_state, icona_specie


def show():
    profile = get_current_profile()
    owner_id = profile["id"]

    st.markdown("## 📅 Appuntamenti")

    tab_prossimi, tab_storico = st.tabs(["📆 Prossimi", "📋 Storico"])

    with tab_prossimi:
        _lista_appuntamenti(owner_id, futuro=True)

    with tab_storico:
        _lista_appuntamenti(owner_id, futuro=False)


def _lista_appuntamenti(owner_id: str, futuro: bool):
    appuntamenti = get_appuntamenti_owner(owner_id, futuro=futuro)
    if not appuntamenti:
        label = "prossimi appuntamenti" if futuro else "appuntamenti nello storico"
        empty_state("📅", f"Nessun {label}")
        return

    for app in appuntamenti:
        animale = app.get("animali") or {}
        vet = app.get("profiles") or {}
        stato = app.get("stato", "in_attesa")

        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.markdown(
                    f"**{format_datetime(app.get('data_ora'))}**  \n"
                    f"{icona_specie(animale.get('specie',''))} **{animale.get('nome','?')}**  \n"
                    f"🩺 {vet.get('nome','')} {vet.get('cognome','')}  \n"
                    f"📝 {app.get('motivo','')}"
                )
            with col2:
                render_badge(stato)
                if app.get("note"):
                    st.caption(app["note"])
            with col3:
                if futuro:
                    if stato == "in_attesa":
                        if st.button("✅ Accetta", key=f"acc_app_{app['id']}"):
                            aggiorna_stato(app["id"], "confermato")
                            st.rerun()
                        if st.button("❌ Rifiuta", key=f"rif_app_{app['id']}"):
                            aggiorna_stato(app["id"], "annullato")
                            st.rerun()
                    elif stato == "confermato":
                        if st.button("❌ Annulla", key=f"ann_app_{app['id']}"):
                            aggiorna_stato(app["id"], "annullato")
                            st.rerun()
            st.divider()
