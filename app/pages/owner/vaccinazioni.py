# pages/owner/vaccinazioni.py
# Libretto vaccinale e terapie del proprietario. I vaccini si scelgono dal catalogo standard.
import streamlit as st
from datetime import date
from app.auth.supabase_auth import get_current_profile
from app.services.animali_service import get_animali_by_owner
from app.services.vaccinazioni_service import get_vaccinazioni, get_terapie, aggiungi_vaccinazione, get_catalogo_vaccini
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

    st.divider()
    tab_vac, tab_ter = st.tabs(["💉 Vaccinazioni", "💊 Terapie in corso"])

    # ── TAB VACCINAZIONI ──────────────────────────────────────────────────────
    with tab_vac:
        _sezione_vaccinazioni(sel_id, animale_sel)

    # ── TAB TERAPIE ───────────────────────────────────────────────────────────
    with tab_ter:
        _sezione_terapie(sel_id)


def _sezione_vaccinazioni(animale_id: str, animale: dict):
    specie = animale.get("specie", "")
    vaccini = get_vaccinazioni(animale_id)

    # ── Bottone aggiungi (fuori dal form per dinamismo) ───────────────────────
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

    # ── Lista vaccinazioni ────────────────────────────────────────────────────
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


def _sezione_terapie(animale_id: str):
    terapie_attive = get_terapie(animale_id, solo_attive=True)
    terapie_passate = get_terapie(animale_id, solo_attive=False)
    terapie_passate = [t for t in terapie_passate if not t.get("attiva")]

    st.markdown("##### 🟢 Terapie in corso")
    if not terapie_attive:
        empty_state("💊", "Nessuna terapia in corso")
    else:
        for t in terapie_attive:
            with st.container():
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
