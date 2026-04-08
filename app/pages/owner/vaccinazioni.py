# pages/owner/vaccinazioni.py
# Libretto vaccinale, terapie, integratori (cavalli) e antiparassitari (cani/gatti).
import streamlit as st
from datetime import date, timedelta
from app.auth.supabase_auth import get_current_profile
from app.services.animali_service import get_animali_by_owner
from app.services.vaccinazioni_service import (
    get_vaccinazioni, get_terapie, aggiungi_vaccinazione, get_catalogo_vaccini,
    get_integratori, aggiungi_integratore, elimina_integratore, INTEGRATORI_CATALOGO,
    get_antiparassitari, aggiungi_antiparassitario, elimina_antiparassitario,
    TIPI_SOMMINISTRAZIONE, COPERTURE_ANTIPARASSITARIO,
)
from app.components.ui_helpers import format_data, empty_state, divisore, icona_specie


def show():
    profile = get_current_profile()
    owner_id = profile["id"]

    st.markdown("## 💉 Vaccinazioni & Terapie")

    animali = get_animali_by_owner(owner_id)
    if not animali:
        empty_state("🐾", "Nessun animale registrato", "Aggiungi prima un animale dalla sezione apposita.")
        return

    # Selettore animale
    nomi = {a["id"]: f"{icona_specie(a['specie'])} {a['nome']}" for a in animali}
    sel_id = st.selectbox("Seleziona animale", options=list(nomi.keys()), format_func=lambda x: nomi[x])
    animale_sel = next(a for a in animali if a["id"] == sel_id)
    specie = animale_sel.get("specie", "")

    st.divider()

    # Tab dinamiche per specie
    if specie == "Cavallo":
        tab_vac, tab_ter, tab_int = st.tabs(["💉 Vaccinazioni", "💊 Terapie in corso", "🌿 Integratori"])
        with tab_vac:
            _sezione_vaccinazioni(sel_id, animale_sel)
        with tab_ter:
            _sezione_terapie(sel_id)
        with tab_int:
            _sezione_integratori(sel_id)
    elif specie in ("Cane", "Gatto"):
        tab_vac, tab_ter, tab_anti = st.tabs(["💉 Vaccinazioni", "💊 Terapie in corso", "🛡️ Antiparassitari"])
        with tab_vac:
            _sezione_vaccinazioni(sel_id, animale_sel)
        with tab_ter:
            _sezione_terapie(sel_id)
        with tab_anti:
            _sezione_antiparassitari(sel_id)
    else:
        tab_vac, tab_ter = st.tabs(["💉 Vaccinazioni", "💊 Terapie in corso"])
        with tab_vac:
            _sezione_vaccinazioni(sel_id, animale_sel)
        with tab_ter:
            _sezione_terapie(sel_id)


# ── VACCINAZIONI ──────────────────────────────────────────────────────────────

def _sezione_vaccinazioni(animale_id: str, animale: dict):
    specie = animale.get("specie", "")
    vaccini = get_vaccinazioni(animale_id)

    if st.button("➕ Aggiungi vaccinazione", key=f"owner_btn_vac_{animale_id}"):
        st.session_state[f"owner_vac_form_{animale_id}"] = True

    if st.session_state.get(f"owner_vac_form_{animale_id}"):
        catalogo = get_catalogo_vaccini(specie)
        opzioni_catalogo = {v["id"]: f"{'🔴' if v['tipo'] == 'obbligatorio' else '🟡'} {v['nome']}" for v in catalogo}
        LIBERO = "__libero__"
        opzioni = {LIBERO: "✏️ Inserisci nome manualmente", **opzioni_catalogo}

        sel_vaccino_id = st.selectbox(
            "Vaccino *",
            options=list(opzioni.keys()),
            format_func=lambda x: opzioni[x],
            key=f"owner_sel_vac_{animale_id}",
        )

        if sel_vaccino_id != LIBERO:
            vac_info = next((v for v in catalogo if v["id"] == sel_vaccino_id), None)
            if vac_info and vac_info.get("descrizione"):
                st.caption(vac_info["descrizione"])

        with st.form(f"owner_form_vac_{animale_id}"):
            if sel_vaccino_id == LIBERO:
                nome_vac = st.text_input("Nome vaccino *")
            else:
                nome_vac = opzioni_catalogo[sel_vaccino_id].split(" ", 1)[1]
                st.markdown(f"**Vaccino selezionato:** {nome_vac}")

            col1, col2 = st.columns(2)
            with col1:
                data_somm = st.date_input(
                    "Data somministrazione *",
                    value=date.today(),
                    max_value=date.today(),
                    key=f"owner_data_somm_{animale_id}",
                )
            with col2:
                data_rich = st.date_input(
                    "Prossimo richiamo",
                    value=None,
                    key=f"owner_data_rich_{animale_id}",
                )
            lotto = st.text_input("Lotto (opzionale)")
            note_v = st.text_input("Note")
            col_s, col_a = st.columns(2)
            with col_s:
                sub_v = st.form_submit_button("💾 Salva", type="primary", use_container_width=True)
            with col_a:
                ann_v = st.form_submit_button("❌ Annulla", use_container_width=True)

        if ann_v:
            st.session_state[f"owner_vac_form_{animale_id}"] = False
            st.rerun()
        if sub_v:
            nome_finale = nome_vac.strip() if sel_vaccino_id == LIBERO else opzioni_catalogo[sel_vaccino_id].split(" ", 1)[1]
            if not nome_finale:
                st.error("Nome vaccino obbligatorio.")
            else:
                ok = aggiungi_vaccinazione({
                    "animale_id": animale_id,
                    "vaccino_catalogo_id": sel_vaccino_id if sel_vaccino_id != LIBERO else None,
                    "nome_vaccino": nome_finale,
                    "data_somministrazione": data_somm.isoformat(),
                    "data_prossimo_richiamo": data_rich.isoformat() if data_rich else None,
                    "lotto": lotto or None,
                    "note": note_v or None,
                })
                if ok:
                    st.session_state[f"owner_vac_form_{animale_id}"] = False
                    st.rerun()
                else:
                    st.error("Errore nel salvataggio.")

    divisore()

    if not vaccini:
        empty_state("💉", "Nessun vaccino registrato")
    else:
        for v in vaccini:
            scaduto = False
            if v.get("data_prossimo_richiamo"):
                try:
                    scaduto = date.fromisoformat(v["data_prossimo_richiamo"]) < date.today()
                except Exception:
                    pass

            colore = "#FDECEA" if scaduto else "#F2EDE7"
            bordo = "#E63946" if scaduto else "#B3A18D"
            scaduto_tag = "<span style='color:#E63946;font-size:0.8rem;'> ⚠️ SCADUTO</span>" if scaduto else ""
            st.markdown(
                f'<div style="background:{colore}; border-left:4px solid {bordo}; padding:0.7rem 1rem; border-radius:0 8px 8px 0; margin-bottom:0.5rem;">'
                f'<b>💉 {v.get("nome_vaccino","")}</b>{scaduto_tag}<br>'
                f'<span style="font-size:0.85rem; color:#555;">'
                f'Somministrato: {format_data(v.get("data_somministrazione"))} &nbsp;|&nbsp; '
                f'Prossimo richiamo: {format_data(v.get("data_prossimo_richiamo"))} &nbsp;|&nbsp; '
                f'Lotto: {v.get("lotto") or "—"}'
                f'</span></div>',
                unsafe_allow_html=True,
            )


# ── TERAPIE ───────────────────────────────────────────────────────────────────

def _sezione_terapie(animale_id: str):
    terapie_attive = get_terapie(animale_id, solo_attive=True)
    terapie_passate = [t for t in get_terapie(animale_id) if not t.get("attiva")]

    st.markdown("##### 🟢 Terapie in corso")
    if not terapie_attive:
        empty_state("💊", "Nessuna terapia in corso")
    else:
        for t in terapie_attive:
            st.markdown(
                f"**💊 {t.get('farmaco','')}** — {t.get('dosaggio','')}  \n"
                f"📅 Dal {format_data(t.get('data_inizio'))}  \n"
                f"📝 {t.get('note') or ''}"
            )

    if terapie_passate:
        with st.expander("📋 Storico terapie"):
            for t in terapie_passate:
                st.markdown(
                    f"**{t.get('farmaco','')}** — dal {format_data(t.get('data_inizio'))} "
                    f"al {format_data(t.get('data_fine'))}"
                )


# ── INTEGRATORI (solo cavalli) ────────────────────────────────────────────────

def _sezione_integratori(animale_id: str):
    integratori = get_integratori(animale_id)

    if st.button("➕ Aggiungi integratore", key=f"btn_int_{animale_id}"):
        st.session_state[f"int_form_{animale_id}"] = True

    if st.session_state.get(f"int_form_{animale_id}"):
        with st.form(f"form_int_{animale_id}"):
            tipo = st.selectbox("Integratore *", INTEGRATORI_CATALOGO, key=f"int_tipo_{animale_id}")
            if tipo == "Altro":
                nome_libero = st.text_input("Nome integratore *", key=f"int_nome_{animale_id}")
            else:
                nome_libero = None
            dosaggio = st.text_input("Dose / frequenza (es. 50g al giorno)", key=f"int_dos_{animale_id}")
            col1, col2 = st.columns(2)
            with col1:
                data_inizio = st.date_input("Data inizio *", value=date.today(), key=f"int_di_{animale_id}")
            with col2:
                data_fine = st.date_input("Data fine (opzionale)", value=None, key=f"int_df_{animale_id}")
            note = st.text_input("Note", key=f"int_note_{animale_id}")
            col_s, col_a = st.columns(2)
            with col_s:
                sub = st.form_submit_button("💾 Salva", type="primary", use_container_width=True)
            with col_a:
                ann = st.form_submit_button("❌ Annulla", use_container_width=True)

        if ann:
            st.session_state[f"int_form_{animale_id}"] = False
            st.rerun()
        if sub:
            nome_finale = (nome_libero or "").strip() if tipo == "Altro" else tipo
            if not nome_finale:
                st.error("Nome integratore obbligatorio.")
            else:
                ok = aggiungi_integratore({
                    "animale_id": animale_id,
                    "farmaco": nome_finale,
                    "dosaggio": dosaggio or None,
                    "data_inizio": data_inizio.isoformat(),
                    "data_fine": data_fine.isoformat() if data_fine else None,
                    "note": note or None,
                    "attiva": True,
                })
                if ok:
                    st.session_state[f"int_form_{animale_id}"] = False
                    st.rerun()
                else:
                    st.error("Errore nel salvataggio.")

    divisore()

    if not integratori:
        empty_state("🌿", "Nessun integratore registrato")
    else:
        for i in integratori:
            attivo = i.get("attiva", True)
            colore = "#F2EDE7" if attivo else "#F5F5F5"
            bordo = "#7D9B6E" if attivo else "#BBBBBB"
            stato_tag = "" if attivo else "<span style='color:#888;font-size:0.8rem;'> · terminato</span>"
            col_card, col_del = st.columns([8, 1])
            with col_card:
                st.markdown(
                    f'<div style="background:{colore}; border-left:4px solid {bordo}; padding:0.7rem 1rem; border-radius:0 8px 8px 0; margin-bottom:0.5rem;">'
                    f'<b>🌿 {i.get("farmaco","")}</b>{stato_tag}<br>'
                    f'<span style="font-size:0.85rem; color:#555;">'
                    f'{i.get("dosaggio") or ""}'
                    f'{" &nbsp;|&nbsp; Dal " + format_data(i.get("data_inizio")) if i.get("data_inizio") else ""}'
                    f'{" al " + format_data(i.get("data_fine")) if i.get("data_fine") else ""}'
                    f'{"  &nbsp;|&nbsp; 📝 " + i.get("note") if i.get("note") else ""}'
                    f'</span></div>',
                    unsafe_allow_html=True,
                )
            with col_del:
                if st.button("🗑️", key=f"del_int_{i['id']}", help="Elimina"):
                    elimina_integratore(i["id"])
                    st.rerun()


# ── ANTIPARASSITARI (cani e gatti) ────────────────────────────────────────────

def _sezione_antiparassitari(animale_id: str):
    antiparassitari = get_antiparassitari(animale_id)

    if st.button("➕ Aggiungi trattamento", key=f"btn_anti_{animale_id}"):
        st.session_state[f"anti_form_{animale_id}"] = True

    if st.session_state.get(f"anti_form_{animale_id}"):
        with st.form(f"form_anti_{animale_id}"):
            col1, col2 = st.columns(2)
            with col1:
                tipo_somm = st.selectbox(
                    "Tipo somministrazione *",
                    TIPI_SOMMINISTRAZIONE,
                    key=f"anti_tipo_{animale_id}",
                )
            with col2:
                copertura = st.selectbox(
                    "Cosa copre *",
                    COPERTURE_ANTIPARASSITARIO,
                    key=f"anti_cop_{animale_id}",
                )
            prodotto = st.text_input("Prodotto usato (es. Frontline, Bravecto)", key=f"anti_prod_{animale_id}")
            col3, col4 = st.columns(2)
            with col3:
                data_somm = st.date_input("Data somministrazione *", value=date.today(), key=f"anti_ds_{animale_id}")
            with col4:
                # Suggerimento prossima dose: +1 mese pipetta/pastiglia, +3 mesi collare
                default_prossima = data_somm + timedelta(days=30) if tipo_somm in ("Pipetta", "Pastiglia") else data_somm + timedelta(days=90)
                data_prossima = st.date_input("Prossima dose", value=default_prossima, key=f"anti_dp_{animale_id}")
            note = st.text_input("Note", key=f"anti_note_{animale_id}")
            col_s, col_a = st.columns(2)
            with col_s:
                sub = st.form_submit_button("💾 Salva", type="primary", use_container_width=True)
            with col_a:
                ann = st.form_submit_button("❌ Annulla", use_container_width=True)

        if ann:
            st.session_state[f"anti_form_{animale_id}"] = False
            st.rerun()
        if sub:
            ok = aggiungi_antiparassitario({
                "animale_id": animale_id,
                "farmaco": prodotto or f"{tipo_somm} antiparassitaria",
                "dosaggio": copertura,
                "tipo_somministrazione": tipo_somm,
                "data_inizio": data_somm.isoformat(),
                "data_prossima_dose": data_prossima.isoformat() if data_prossima else None,
                "note": note or None,
                "attiva": True,
            })
            if ok:
                st.session_state[f"anti_form_{animale_id}"] = False
                st.rerun()
            else:
                st.error("Errore nel salvataggio.")

    divisore()

    if not antiparassitari:
        empty_state("🛡️", "Nessun trattamento registrato")
    else:
        oggi = date.today()
        for a in antiparassitari:
            prossima = None
            in_scadenza = False
            scaduto = False
            if a.get("data_prossima_dose"):
                try:
                    prossima = date.fromisoformat(a["data_prossima_dose"])
                    scaduto = prossima < oggi
                    in_scadenza = not scaduto and (prossima - oggi).days <= 7
                except Exception:
                    pass

            if scaduto:
                colore, bordo = "#FDECEA", "#E63946"
                badge = "<span style='color:#E63946;font-size:0.8rem;'> ⚠️ DA RINNOVARE</span>"
            elif in_scadenza:
                colore, bordo = "#FFF8E1", "#F4A261"
                badge = "<span style='color:#F4A261;font-size:0.8rem;'> ⏰ IN SCADENZA</span>"
            else:
                colore, bordo = "#F2EDE7", "#B3A18D"
                badge = ""

            icona_tipo = {"Pipetta": "💧", "Pastiglia": "💊", "Spray": "🌬️", "Collare": "🔗"}.get(
                a.get("tipo_somministrazione", ""), "🛡️"
            )

            col_card, col_del = st.columns([8, 1])
            with col_card:
                st.markdown(
                    f'<div style="background:{colore}; border-left:4px solid {bordo}; padding:0.7rem 1rem; border-radius:0 8px 8px 0; margin-bottom:0.5rem;">'
                    f'<b>{icona_tipo} {a.get("farmaco","")} — {a.get("tipo_somministrazione","")}</b>{badge}<br>'
                    f'<span style="font-size:0.85rem; color:#555;">'
                    f'Copre: {a.get("dosaggio") or "—"} &nbsp;|&nbsp; '
                    f'Somministrato: {format_data(a.get("data_inizio"))} &nbsp;|&nbsp; '
                    f'Prossima dose: {format_data(a.get("data_prossima_dose"))}'
                    f'{"  &nbsp;|&nbsp; 📝 " + a.get("note") if a.get("note") else ""}'
                    f'</span></div>',
                    unsafe_allow_html=True,
                )
            with col_del:
                if st.button("🗑️", key=f"del_anti_{a['id']}", help="Elimina"):
                    elimina_antiparassitario(a["id"])
                    st.rerun()
