# pages/vet/cartella_clinica.py
# Cartelle cliniche: il vet aggiunge visite, diagnosi, prescrizioni per ogni animale.
import streamlit as st
from datetime import date, datetime
from app.auth.supabase_auth import get_current_profile
from app.services.animali_service import get_animali_by_vet
from app.services.cartella_clinica_service import (
    get_cartelle_by_animale, crea_cartella, elimina_cartella,
)
from app.components.ui_helpers import format_datetime, empty_state, icona_specie, divisore


def show():
    profile = get_current_profile()
    vet_id = profile["id"]

    st.markdown("## 📋 Cartelle Cliniche")

    animali = get_animali_by_vet(vet_id)
    if not animali:
        empty_state("🐾", "Nessun paziente")
        return

    # Filtri
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_specie = st.selectbox("Filtra per specie", ["Tutte", "Cane", "Gatto", "Cavallo"])
    with col2:
        cerca = st.text_input("Cerca per nome animale o proprietario", placeholder="🔍")
    with col3:
        st.markdown(f"**{len(animali)} pazienti totali**")

    # Applica filtri
    filtrati = animali
    if filtro_specie != "Tutte":
        filtrati = [a for a in filtrati if a.get("specie") == filtro_specie]
    if cerca:
        q = cerca.lower()
        filtrati = [
            a for a in filtrati
            if q in (a.get("nome") or "").lower()
            or q in (a.get("profiles", {}) or {}).get("cognome", "").lower()
            or q in (a.get("profiles", {}) or {}).get("nome", "").lower()
        ]

    if not filtrati:
        empty_state("🔍", "Nessun risultato trovato")
        return

    for animale in filtrati:
        specie = animale.get("specie", "")
        owner = animale.get("profiles") or {}
        with st.expander(
            f"{icona_specie(specie)} **{animale['nome']}** — "
            f"{animale.get('razza', '?')} · "
            f"👤 {owner.get('nome', '')} {owner.get('cognome', '')}"
        ):
            render_cartella_animale(animale["id"], vet_id)


def render_cartella_animale(animale_id: str, vet_id: str):
    """Componente riutilizzabile — mostra e permette di aggiungere cartelle per un animale."""

    if st.button("➕ Nuova visita / cartella", key=f"new_cart_{animale_id}", type="primary"):
        st.session_state[f"cart_form_{animale_id}"] = True

    if st.session_state.get(f"cart_form_{animale_id}"):
        _form_cartella(animale_id, vet_id)
        divisore()

    cartelle = get_cartelle_by_animale(animale_id)
    if not cartelle:
        empty_state("📋", "Nessuna cartella clinica ancora")
        return

    for c in cartelle:
        with st.expander(
            f"📋 {format_datetime(c.get('data_visita'))} — {c.get('diagnosi','')[:60]}",
            expanded=False,
        ):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**Data visita:** {format_datetime(c.get('data_visita'))}")
                st.markdown(f"**Anamnesi:** {c.get('anamnesi') or '—'}")
                st.markdown(f"**Diagnosi:** {c.get('diagnosi') or '—'}")
                st.markdown(f"**Terapia prescritta:** {c.get('terapia_prescritta') or '—'}")
                st.markdown(f"**Peso rilevato:** {c.get('peso_kg') or '—'} kg")
                st.markdown(f"**Temperatura:** {c.get('temperatura') or '—'} °C")
                if c.get("note"):
                    st.markdown(f"**Note:** {c['note']}")
                if c.get("prescrizione_digitale"):
                    st.info(f"📄 **Prescrizione:** {c['prescrizione_digitale']}")
            with col2:
                if st.button("🗑️ Elimina", key=f"del_cart_{c['id']}"):
                    elimina_cartella(c["id"])
                    st.rerun()


def _form_cartella(animale_id: str, vet_id: str):
    st.markdown("#### ➕ Nuova cartella clinica")
    with st.form(f"form_cart_{animale_id}"):
        col1, col2 = st.columns(2)
        with col1:
            data_visita = st.date_input("Data visita *", value=date.today(), max_value=date.today())
            ora_visita = st.time_input("Ora visita", value=datetime.now().time())
        with col2:
            peso = st.number_input("Peso rilevato (kg)", min_value=0.0, step=0.1)
            temperatura = st.number_input("Temperatura (°C)", min_value=35.0, max_value=43.0, step=0.1, value=38.5)

        anamnesi = st.text_area("Anamnesi *", height=100, placeholder="Descrizione dei sintomi riferiti dal proprietario…")
        diagnosi = st.text_area("Diagnosi *", height=80, placeholder="es. Otite esterna batterica")
        terapia = st.text_area("Terapia prescritta", height=80, placeholder="es. Amoxicillina 20mg/kg 2 volte al giorno per 7 giorni")
        prescrizione = st.text_area("Prescrizione digitale (opzionale)", height=60)
        note = st.text_area("Note aggiuntive", height=60)

        col_s, col_a = st.columns(2)
        with col_s:
            sub = st.form_submit_button("💾 Salva cartella", type="primary", use_container_width=True)
        with col_a:
            ann = st.form_submit_button("❌ Annulla", use_container_width=True)

    if ann:
        st.session_state[f"cart_form_{animale_id}"] = False
        st.rerun()

    if sub:
        if not anamnesi or not diagnosi:
            st.error("Anamnesi e diagnosi sono obbligatorie.")
            return
        data_ora = datetime.combine(data_visita, ora_visita).isoformat()
        ok = crea_cartella({
            "animale_id": animale_id,
            "vet_id": vet_id,
            "data_visita": data_ora,
            "peso_kg": peso or None,
            "temperatura": temperatura or None,
            "anamnesi": anamnesi,
            "diagnosi": diagnosi,
            "terapia_prescritta": terapia or None,
            "prescrizione_digitale": prescrizione or None,
            "note": note or None,
        })
        if ok:
            st.success("✅ Cartella clinica salvata!")
            st.session_state[f"cart_form_{animale_id}"] = False
            st.rerun()
        else:
            st.error("Errore nel salvataggio.")
