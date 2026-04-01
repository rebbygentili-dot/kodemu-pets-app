"""
pages/vet/pazienti.py
Lista pazienti (animali) del veterinario con filtri e gestione completa.
"""
import streamlit as st
from datetime import date
from app.auth.supabase_auth import get_current_profile
from app.services.animali_service import get_animali_by_vet
from app.services.vaccinazioni_service import (
    get_vaccinazioni, aggiungi_vaccinazione, elimina_vaccinazione,
    get_terapie, aggiungi_terapia, termina_terapia, elimina_terapia,
)
from app.services.cartella_clinica_service import get_cartelle_by_animale
from app.services.documenti_service import (
    get_documenti, upload_documento, elimina_documento,
    get_url_documento, TIPI_DOCUMENTO,
)
from app.components.ui_helpers import (
    format_data, format_datetime, empty_state, icona_specie, divisore
)

ICONE_TIPO = {
    "Referto": "📄",
    "Radiografia": "🔬",
    "Ecografia": "🔬",
    "Ricetta": "💊",
    "Fattura": "🧾",
    "Vaccinazione": "💉",
    "Altro": "📎",
}


def show():
    profile = get_current_profile()
    vet_id = profile["id"]

    st.markdown("## 🐾 I miei pazienti")

    animali = get_animali_by_vet(vet_id)
    if not animali:
        empty_state("🐾", "Nessun paziente ancora", "I pazienti appariranno quando un proprietario si collega.")
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
            f"{animale.get('razza','?')} · "
            f"👤 {owner.get('nome','')} {owner.get('cognome','')}"
        ):
            tab_info, tab_cartella, tab_vaccini, tab_terapie, tab_documenti = st.tabs(
                ["ℹ️ Info", "📋 Cartella clinica", "💉 Vaccinazioni", "💊 Terapie", "📄 Documenti"]
            )

            with tab_info:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Specie:** {specie}")
                    st.markdown(f"**Razza:** {animale.get('razza','—')}")
                    st.markdown(f"**Data nascita:** {format_data(animale.get('data_nascita'))}")
                    st.markdown(f"**Sesso:** {animale.get('sesso','—')}")
                with col2:
                    st.markdown(f"**Microchip:** {animale.get('microchip') or '—'}")
                    st.markdown(f"**Peso:** {animale.get('peso_kg') or '—'} kg")
                    st.markdown(f"**Allergie:** {animale.get('allergie') or '—'}")
                    st.markdown(f"**Proprietario:** {owner.get('nome','')} {owner.get('cognome','')} — {owner.get('email','')}")

            with tab_cartella:
                from app.pages.vet.cartella_clinica import render_cartella_animale
                render_cartella_animale(animale["id"], vet_id)

            with tab_vaccini:
                _tab_vaccini(animale)

            with tab_terapie:
                _tab_terapie(animale)

            with tab_documenti:
                _tab_documenti(animale)


def _tab_vaccini(animale: dict):
    animale_id = animale["id"]
    vaccini = get_vaccinazioni(animale_id)

    # Bottone aggiungi (fuori dal form)
    if st.button("➕ Aggiungi vaccino", key=f"btn_vac_{animale_id}"):
        st.session_state[f"vac_form_{animale_id}"] = True

    if st.session_state.get(f"vac_form_{animale_id}"):
        with st.form(f"form_vac_{animale_id}"):
            nome_vac = st.text_input("Nome vaccino *")
            col1, col2 = st.columns(2)
            with col1:
                data_somm = st.date_input(
                    "Data somministrazione *",
                    value=date.today(),
                    max_value=date.today(),
                    key=f"data_somm_{animale_id}",
                )
            with col2:
                data_rich = st.date_input(
                    "Prossimo richiamo",
                    value=None,
                    key=f"data_rich_{animale_id}",
                )
            lotto = st.text_input("Lotto (opzionale)")
            note_v = st.text_input("Note")
            col_s, col_a = st.columns(2)
            with col_s:
                sub_v = st.form_submit_button("💾 Salva", type="primary", use_container_width=True)
            with col_a:
                ann_v = st.form_submit_button("❌ Annulla", use_container_width=True)

        if ann_v:
            st.session_state[f"vac_form_{animale_id}"] = False
            st.rerun()
        if sub_v:
            if not nome_vac:
                st.error("Nome vaccino obbligatorio.")
            else:
                ok = aggiungi_vaccinazione({
                    "animale_id": animale_id,
                    "nome_vaccino": nome_vac,
                    "data_somministrazione": data_somm.isoformat(),
                    "data_prossimo_richiamo": data_rich.isoformat() if data_rich else None,
                    "lotto": lotto or None,
                    "note": note_v or None,
                })
                if ok:
                    st.session_state[f"vac_form_{animale_id}"] = False
                    st.rerun()
                else:
                    st.error("Errore nel salvataggio.")

    # Lista vaccini con delete
    if not vaccini:
        empty_state("💉", "Nessun vaccino registrato")
    else:
        for v in vaccini:
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(
                    f"**{v.get('nome_vaccino','')}** — "
                    f"somministrato: {format_data(v.get('data_somministrazione'))} — "
                    f"prossimo richiamo: {format_data(v.get('data_prossimo_richiamo'))}"
                )
            with col2:
                if st.button("🗑️", key=f"del_vac_vet_{v['id']}", help="Elimina vaccino"):
                    elimina_vaccinazione(v["id"])
                    st.rerun()


def _tab_terapie(animale: dict):
    animale_id = animale["id"]
    terapie_attive = get_terapie(animale_id, solo_attive=True)
    terapie_passate = get_terapie(animale_id, solo_attive=False)
    terapie_passate = [t for t in terapie_passate if not t.get("attiva")]

    # Bottone aggiungi (fuori dal form)
    if st.button("➕ Aggiungi terapia", key=f"btn_ter_{animale_id}"):
        st.session_state[f"ter_form_{animale_id}"] = True

    if st.session_state.get(f"ter_form_{animale_id}"):
        with st.form(f"form_ter_{animale_id}"):
            farmaco = st.text_input("Farmaco / Trattamento *")
            dosaggio = st.text_input("Dosaggio", placeholder="es. 1 compressa 2 volte al giorno")
            data_inizio = st.date_input(
                "Data inizio *",
                value=date.today(),
                max_value=date.today(),
                key=f"data_inizio_{animale_id}",
            )
            note_t = st.text_area("Note", height=80)
            col_s, col_a = st.columns(2)
            with col_s:
                sub_t = st.form_submit_button("💾 Salva", type="primary", use_container_width=True)
            with col_a:
                ann_t = st.form_submit_button("❌ Annulla", use_container_width=True)

        if ann_t:
            st.session_state[f"ter_form_{animale_id}"] = False
            st.rerun()
        if sub_t:
            if not farmaco:
                st.error("Il nome del farmaco è obbligatorio.")
            else:
                ok = aggiungi_terapia({
                    "animale_id": animale_id,
                    "farmaco": farmaco,
                    "dosaggio": dosaggio or None,
                    "data_inizio": data_inizio.isoformat(),
                    "attiva": True,
                    "note": note_t or None,
                })
                if ok:
                    st.session_state[f"ter_form_{animale_id}"] = False
                    st.rerun()
                else:
                    st.error("Errore nel salvataggio.")

    # Terapie attive con termina/elimina
    st.markdown("##### 🟢 Terapie in corso")
    if not terapie_attive:
        empty_state("💊", "Nessuna terapia in corso")
    else:
        for t in terapie_attive:
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(
                    f"**{t.get('farmaco','')}** — {t.get('dosaggio','—')}  \n"
                    f"📅 Dal {format_data(t.get('data_inizio'))}  \n"
                    f"📝 {t.get('note') or ''}"
                )
            with col2:
                if st.button("✅ Termina", key=f"end_ter_vet_{t['id']}"):
                    termina_terapia(t["id"])
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"del_ter_vet_{t['id']}", help="Elimina terapia"):
                    elimina_terapia(t["id"])
                    st.rerun()

    if terapie_passate:
        with st.expander("📋 Storico terapie"):
            for t in terapie_passate:
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(
                        f"**{t.get('farmaco','')}** — dal {format_data(t.get('data_inizio'))} "
                        f"al {format_data(t.get('data_fine'))}"
                    )
                with col2:
                    if st.button("🗑️", key=f"del_ter_past_vet_{t['id']}", help="Elimina terapia"):
                        elimina_terapia(t["id"])
                        st.rerun()


def _tab_documenti(animale: dict):
    animale_id = animale["id"]
    owner_id = animale.get("owner_id", "")

    # Upload
    with st.expander("📤 Carica documento", expanded=False):
        with st.form(f"form_upload_doc_{animale_id}"):
            file = st.file_uploader(
                "Seleziona file (PDF o immagine)",
                type=["pdf", "jpg", "jpeg", "png", "webp"],
                help="Max 25 MB",
            )
            col1, col2 = st.columns(2)
            with col1:
                tipo = st.selectbox("Tipo documento", TIPI_DOCUMENTO)
            with col2:
                note_doc = st.text_input("Note (opzionale)")
            sub_doc = st.form_submit_button("📤 Carica", type="primary", use_container_width=True)

        if sub_doc:
            if not file:
                st.error("Seleziona un file.")
            else:
                with st.spinner("Caricamento in corso…"):
                    risultato = upload_documento(
                        file_bytes=file.read(),
                        filename=file.name,
                        content_type=file.type,
                        animale_id=animale_id,
                        tipo=tipo,
                        note=note_doc,
                        owner_id=owner_id,
                    )
                if risultato:
                    st.success(f"✅ Documento '{file.name}' caricato!")
                    st.rerun()
                else:
                    st.error("Errore nel caricamento.")

    # Lista documenti
    documenti = get_documenti(animale_id)

    if not documenti:
        empty_state("📁", "Nessun documento", "Carica referti, ricette o altri file dal pannello sopra.")
        return

    for doc in documenti:
        icona = ICONE_TIPO.get(doc.get("tipo", "Altro"), "📎")
        col1, col2, col3 = st.columns([4, 2, 1])
        with col1:
            st.markdown(
                f"{icona} **{doc.get('nome_file','')}**  \n"
                f"<span style='font-size:0.83rem;color:#666;'>"
                f"Tipo: {doc.get('tipo','')} &nbsp;·&nbsp; {format_datetime(doc.get('created_at'))}"
                f"</span>",
                unsafe_allow_html=True,
            )
            if doc.get("note"):
                st.caption(doc["note"])
        with col2:
            url = get_url_documento(doc.get("storage_path", ""))
            if url:
                st.link_button("⬇️ Scarica", url)
        with col3:
            if st.button("🗑️", key=f"del_doc_vet_{doc['id']}", help="Elimina documento"):
                elimina_documento(doc["id"], doc.get("storage_path", ""))
                st.rerun()
        st.divider()
