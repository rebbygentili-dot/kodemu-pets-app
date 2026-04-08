# pages/owner/dashboard.py
# Dashboard owner: vaccini in scadenza, prossimi appuntamenti, riepilogo animali.
import streamlit as st
from app.auth.supabase_auth import get_current_profile
from app.services.animali_service import get_animali_by_owner
from app.services.appuntamenti_service import get_appuntamenti_owner
from app.services.vaccinazioni_service import get_vaccinazioni_in_scadenza
from app.services.messaggi_service import get_messaggi_non_letti
from app.components.ui_helpers import card_metrica, icona_specie, format_datetime, empty_state, divisore


def show():
    profile = get_current_profile()
    user_id = profile["id"]
    nome = profile.get("nome", "")

    st.markdown(f"## 👋 Ciao, {nome}!")
    st.markdown("Ecco il riepilogo della salute dei tuoi animali.")

    # ── Metriche rapide ───────────────────────────────────────────────────────
    animali = get_animali_by_owner(user_id)
    appuntamenti = get_appuntamenti_owner(user_id, futuro=True)
    scadenze = get_vaccinazioni_in_scadenza(user_id, giorni=30)
    msg_non_letti = get_messaggi_non_letti(user_id)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        card_metrica("I miei animali", len(animali), "🐾")
    with col2:
        card_metrica("Prossimi appuntamenti", len(appuntamenti), "📅")
    with col3:
        card_metrica("Vaccini in scadenza", len(scadenze), "💉", colore="#E63946" if scadenze else "#B3A18D")
    with col4:
        card_metrica("Messaggi non letti", msg_non_letti, "💬", colore="#E76F51" if msg_non_letti else "#B3A18D")

    divisore()

    # ── Sezione animali ───────────────────────────────────────────────────────
    st.markdown("### 🐾 I miei animali")
    if not animali:
        empty_state("🐾", "Nessun animale registrato", "Vai su 'I miei animali' per aggiungerne uno!")
    else:
        cols = st.columns(min(len(animali), 3))
        for i, animale in enumerate(animali):
            with cols[i % 3]:
                specie = animale.get("specie", "")
                st.markdown(
                    f"""
                    <div style="background:#fff; border:1px solid #e0e0e0; border-radius:12px;
                                padding:1rem; margin-bottom:0.5rem; box-shadow:0 1px 4px #0001;">
                        <div style="font-size:2rem; text-align:center;">{icona_specie(specie)}</div>
                        <div style="font-weight:700; text-align:center; font-size:1.1rem;">{animale.get("nome", "")}</div>
                        <div style="color:#666; text-align:center; font-size:0.85rem;">{specie} · {animale.get("razza","")}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    divisore()

    # ── Prossimi appuntamenti ─────────────────────────────────────────────────
    st.markdown("### 📅 Prossimi appuntamenti")
    if not appuntamenti:
        empty_state("📅", "Nessun appuntamento imminente")
    else:
        for app in appuntamenti[:5]:
            st.markdown(
                f"""
                <div style="background:#F2EDE7; border-left:4px solid #B3A18D;
                            padding:0.7rem 1rem; border-radius:0 8px 8px 0; margin-bottom:0.4rem;">
                    <b>{format_datetime(app.get('data_ora'))}</b> —
                    {app.get('animali', {}).get('nome', '?')} •
                    <span style="color:#555;">{app.get('motivo','')}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Vaccini in scadenza ───────────────────────────────────────────────────
    if scadenze:
        divisore()
        st.markdown("### ⚠️ Vaccini in scadenza")
        for v in scadenze:
            st.warning(
                f"**{v.get('nome_vaccino','')}** per **{v.get('animali',{}).get('nome','?')}** "
                f"— scadenza: {v.get('data_prossimo_richiamo','')}"
            )
