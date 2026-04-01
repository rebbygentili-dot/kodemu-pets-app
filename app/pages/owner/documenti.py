"""
pages/owner/documenti.py
Visualizzazione documenti (referti, ricette, fatture…) in sola lettura.
"""
import streamlit as st
from app.auth.supabase_auth import get_current_profile
from app.services.animali_service import get_animali_by_owner
from app.services.documenti_service import (
    get_documenti, get_url_documento,
)
from app.components.ui_helpers import format_datetime, empty_state, icona_specie


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
    owner_id = profile["id"]

    st.markdown("## 📁 Documenti")

    animali = get_animali_by_owner(owner_id)
    if not animali:
        empty_state("🐾", "Nessun animale registrato")
        return

    nomi = {a["id"]: f"{icona_specie(a['specie'])} {a['nome']}" for a in animali}
    sel_id = st.selectbox("Seleziona animale", options=list(nomi.keys()), format_func=lambda x: nomi[x])

    st.divider()

    # ── Lista documenti ───────────────────────────────────────────────────────
    documenti = get_documenti(sel_id)

    if not documenti:
        empty_state("📁", "Nessun documento", "Il veterinario non ha ancora caricato documenti per questo animale.")
        return

    # Filtro per tipo
    tipi_presenti = list(set(d.get("tipo", "Altro") for d in documenti))
    filtro = st.multiselect("Filtra per tipo", tipi_presenti, default=tipi_presenti)

    for doc in documenti:
        if doc.get("tipo") not in filtro:
            continue
        icona = ICONE_TIPO.get(doc.get("tipo", "Altro"), "📎")

        col1, col2 = st.columns([5, 2])
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
        st.divider()
