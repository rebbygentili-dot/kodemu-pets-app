"""
pages/owner/vaccinazioni.py
Libretto vaccinale e terapie in corso per il proprietario (sola lettura).
"""
import streamlit as st
from datetime import date
from app.auth.supabase_auth import get_current_profile
from app.services.animali_service import get_animali_by_owner, get_vaccini_consigliati
from app.services.vaccinazioni_service import get_vaccinazioni, get_terapie
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
    vaccini = get_vaccinazioni(animale_id)
    specie = animale.get("specie", "")

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

            colore = "#FDECEA" if scaduto else "#F0F7F3"
            bordo = "#E63946" if scaduto else "#2D6A4F"

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

    # Vaccini consigliati per la specie
    consigliati = get_vaccini_consigliati(specie)
    if consigliati:
        divisore("💡 Vaccini consigliati per questa specie")
        for vc in consigliati:
            st.markdown(f"- {vc}")


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
