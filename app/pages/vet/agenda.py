"""
pages/vet/agenda.py
Agenda appuntamenti del veterinario con gestione stati e creazione appuntamenti.
"""
import streamlit as st
from datetime import date, time, timedelta, datetime
from app.auth.supabase_auth import get_current_profile
from app.services.appuntamenti_service import (
    get_appuntamenti_vet, aggiorna_stato, crea_appuntamento, STATI, STATI_LABEL
)
from app.services.collegamenti_service import get_collegamenti_vet
from app.services.animali_service import get_animali_by_vet
from app.components.ui_helpers import format_datetime, render_badge, empty_state, icona_specie


def show():
    profile = get_current_profile()
    vet_id = profile["id"]

    st.markdown("## 📅 Agenda")

    # ── Bottone nuovo appuntamento ────────────────────────────────────────────
    if st.button("➕ Nuovo appuntamento", type="primary"):
        st.session_state["agenda_form"] = True

    if st.session_state.get("agenda_form"):
        _form_nuovo_appuntamento(vet_id)
        st.divider()

    # ── Filtri ────────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        data_da = st.date_input("Dal", value=date.today())
    with col2:
        data_a = st.date_input("Al", value=date.today() + timedelta(days=30))
    with col3:
        filtro_stato = st.selectbox("Stato", ["Tutti"] + list(STATI_LABEL.values()))

    appuntamenti = get_appuntamenti_vet(
        vet_id,
        data_da=data_da.isoformat() + "T00:00:00",
        data_a=data_a.isoformat() + "T23:59:59",
    )

    # Filtro stato
    if filtro_stato != "Tutti":
        stato_key = next((k for k, v in STATI_LABEL.items() if v == filtro_stato), None)
        if stato_key:
            appuntamenti = [a for a in appuntamenti if a.get("stato") == stato_key]

    st.markdown(f"**{len(appuntamenti)} appuntamenti trovati**")
    st.divider()

    if not appuntamenti:
        empty_state("📅", "Nessun appuntamento nel periodo selezionato")
        return

    for app in appuntamenti:
        animale = app.get("animali") or {}
        owner = app.get("profiles") or {}
        stato = app.get("stato", "in_attesa")

        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            st.markdown(
                f"**{format_datetime(app.get('data_ora'))}**  \n"
                f"{icona_specie(animale.get('specie',''))} **{animale.get('nome','?')}**  \n"
                f"👤 {owner.get('nome','')} {owner.get('cognome','')} — {owner.get('email','')}  \n"
                f"📝 {app.get('motivo','')}"
            )
        with col2:
            render_badge(stato)
            if app.get("note"):
                st.caption(f"Note: {app['note']}")
        with col3:
            # Cambio stato rapido
            if stato == "in_attesa":
                if st.button("✅ Conferma", key=f"conf_{app['id']}"):
                    aggiorna_stato(app["id"], "confermato")
                    st.rerun()
                if st.button("❌ Annulla", key=f"ann_{app['id']}"):
                    aggiorna_stato(app["id"], "annullato")
                    st.rerun()
            elif stato == "confermato":
                if st.button("🏁 Completato", key=f"comp_{app['id']}", type="primary"):
                    aggiorna_stato(app["id"], "completato")
                    st.rerun()
                if st.button("❌ Annulla", key=f"ann2_{app['id']}"):
                    aggiorna_stato(app["id"], "annullato")
                    st.rerun()
        st.divider()


def _form_nuovo_appuntamento(vet_id: str):
    st.markdown("### ➕ Nuovo appuntamento")

    collegamenti = get_collegamenti_vet(vet_id)
    if not collegamenti:
        st.warning("⚠️ Non hai proprietari collegati. Accetta prima una richiesta di collegamento.")
        if st.button("❌ Chiudi", key="chiudi_form_no_owner"):
            st.session_state["agenda_form"] = False
            st.rerun()
        return

    # Selectbox proprietario FUORI dal form per filtrare dinamicamente gli animali
    nomi_owner = {
        c["owner_id"]: f"👤 {c['profiles']['nome']} {c['profiles']['cognome']}"
        for c in collegamenti if c.get("profiles")
    }
    owner_sel = st.selectbox(
        "Proprietario *",
        options=list(nomi_owner.keys()),
        format_func=lambda x: nomi_owner[x],
        key="form_app_owner_sel",
    )

    # Prendi tutti gli animali del vet e filtra per owner selezionato
    animali_tutti = get_animali_by_vet(vet_id)
    animali_owner = [a for a in animali_tutti if a.get("owner_id") == owner_sel]

    with st.form("form_nuovo_app_vet"):
        if not animali_owner:
            st.warning("Nessun animale trovato per questo proprietario.")
            st.form_submit_button("❌ Annulla")
        else:
            nomi_animali = {
                a["id"]: f"{icona_specie(a['specie'])} {a['nome']}"
                for a in animali_owner
            }
            animale_id = st.selectbox(
                "Animale *",
                options=list(nomi_animali.keys()),
                format_func=lambda x: nomi_animali[x],
            )

            col1, col2 = st.columns(2)
            with col1:
                data_app = st.date_input("Data *", min_value=date.today())
            with col2:
                ora_app = st.time_input("Ora *", value=time(9, 0))

            motivo = st.text_input("Motivo *", placeholder="es. Visita di controllo, Vaccino annuale…")
            note = st.text_area("Note", height=80)

            col_s, col_a = st.columns(2)
            with col_s:
                sub = st.form_submit_button("📅 Crea appuntamento", type="primary", use_container_width=True)
            with col_a:
                ann = st.form_submit_button("❌ Annulla", use_container_width=True)

            if ann:
                st.session_state["agenda_form"] = False
                st.rerun()

            if sub:
                if not motivo:
                    st.error("Il motivo è obbligatorio.")
                else:
                    data_ora = datetime.combine(data_app, ora_app).isoformat()
                    ok = crea_appuntamento({
                        "owner_id": owner_sel,
                        "vet_id": vet_id,
                        "animale_id": animale_id,
                        "data_ora": data_ora,
                        "motivo": motivo,
                        "note": note or None,
                        "stato": "in_attesa",
                    })
                    if ok:
                        st.success("✅ Appuntamento creato! Il proprietario dovrà confermarlo.")
                        st.session_state["agenda_form"] = False
                        st.rerun()
                    else:
                        st.error("Errore nella creazione dell'appuntamento.")
