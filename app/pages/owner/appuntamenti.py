"""
pages/owner/appuntamenti.py
Prenotazione visite e storico appuntamenti per il proprietario.
"""
import streamlit as st
from datetime import date, datetime, time
from app.auth.supabase_auth import get_current_profile
from app.services.animali_service import get_animali_by_owner
from app.services.appuntamenti_service import (
    get_appuntamenti_owner, crea_appuntamento, elimina_appuntamento,
    ha_appuntamento_attivo, STATI_LABEL,
)
from app.services.collegamenti_service import get_collegamenti_owner
from app.components.ui_helpers import format_datetime, render_badge, empty_state, icona_specie


def show():
    profile = get_current_profile()
    owner_id = profile["id"]

    st.markdown("## 📅 Appuntamenti")

    tab_prossimi, tab_storico, tab_nuovo = st.tabs(
        ["📆 Prossimi", "📋 Storico", "➕ Nuovo appuntamento"]
    )

    with tab_prossimi:
        _lista_appuntamenti(owner_id, futuro=True)

    with tab_storico:
        _lista_appuntamenti(owner_id, futuro=False)

    with tab_nuovo:
        _form_nuovo_appuntamento(owner_id)


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
            col1, col2, col3 = st.columns([3, 2, 1])
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
                if futuro and stato in ("in_attesa", "confermato"):
                    if st.button("❌", key=f"del_app_{app['id']}", help="Annulla appuntamento"):
                        elimina_appuntamento(app["id"])
                        st.rerun()
            st.divider()


def _form_nuovo_appuntamento(owner_id: str):
    animali = get_animali_by_owner(owner_id)
    if not animali:
        empty_state("🐾", "Nessun animale registrato", "Aggiungi prima un animale.")
        return

    collegamenti = get_collegamenti_owner(owner_id)
    vet_accettati = [c for c in collegamenti if c.get("stato") == "accepted"]

    st.markdown("### ➕ Prenota un appuntamento")

    with st.form("form_app"):
        # Selezione animale
        nomi_animali = {a["id"]: f"{icona_specie(a['specie'])} {a['nome']}" for a in animali}
        animale_id = st.selectbox("Animale *", options=list(nomi_animali.keys()),
                                   format_func=lambda x: nomi_animali[x])

        # Selezione veterinario
        if not vet_accettati:
            st.warning("⚠️ Non hai nessun veterinario collegato. Collegati prima a un veterinario dalla sezione 'Il mio veterinario'.")
            vet_id = None
        else:
            nomi_vet = {
                c["vet_id"]: f"🩺 {c['profiles']['nome']} {c['profiles']['cognome']}"
                for c in vet_accettati if c.get("profiles")
            }
            vet_id = st.selectbox("Veterinario *", options=list(nomi_vet.keys()),
                                   format_func=lambda x: nomi_vet[x])

        col1, col2 = st.columns(2)
        with col1:
            data_app = st.date_input("Data *", min_value=date.today())
        with col2:
            ora_app = st.time_input("Ora *", value=time(9, 0))

        motivo = st.text_input("Motivo della visita *", placeholder="es. Visita di controllo, Vaccino annuale…")
        note = st.text_area("Note aggiuntive", height=80)

        sub = st.form_submit_button("📅 Prenota", type="primary", use_container_width=True)

    if sub:
        if not motivo:
            st.error("Il motivo della visita è obbligatorio.")
            return
        if not vet_id:
            st.error("Seleziona un veterinario.")
            return

        data_ora = datetime.combine(data_app, ora_app).isoformat()

        if ha_appuntamento_attivo(owner_id, vet_id, animale_id, data_ora):
            st.warning("⚠️ Hai già un appuntamento in attesa o confermato per questo animale, veterinario e orario.")
            return

        ok = crea_appuntamento({
            "owner_id": owner_id,
            "vet_id": vet_id,
            "animale_id": animale_id,
            "data_ora": data_ora,
            "motivo": motivo,
            "note": note or None,
            "stato": "in_attesa",
        })
        if ok:
            st.success("✅ Appuntamento prenotato! Il veterinario riceverà la richiesta.")
            st.rerun()
        else:
            st.error("Errore nella prenotazione.")
