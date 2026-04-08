# pages/vet/dashboard.py
# Dashboard vet: appuntamenti di oggi, ultimi pazienti, richieste di collegamento in attesa.
import streamlit as st
from datetime import date
from app.auth.supabase_auth import get_current_profile
from app.services.animali_service import get_animali_by_vet
from app.services.appuntamenti_service import get_appuntamenti_oggi, get_appuntamenti_vet
from app.services.collegamenti_service import get_richieste_vet, get_collegamenti_vet
from app.services.cartella_clinica_service import get_ultime_visite_vet
from app.services.messaggi_service import get_messaggi_non_letti
from app.components.ui_helpers import card_metrica, format_datetime, empty_state, divisore, render_badge, icona_specie


def show():
    profile = get_current_profile()
    vet_id = profile["id"]
    nome = profile.get("nome", "")

    st.markdown(f"## 👋 Buongiorno, Dr. {nome}!")
    st.markdown(f"**{date.today().strftime('%A %d %B %Y')}**")

    # ── Metriche ──────────────────────────────────────────────────────────────
    pazienti = get_animali_by_vet(vet_id)
    app_oggi = get_appuntamenti_oggi(vet_id)
    richieste = get_richieste_vet(vet_id)
    msg_non_letti = get_messaggi_non_letti(vet_id)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        card_metrica("Pazienti totali", len(pazienti), "🐾")
    with col2:
        card_metrica("Appuntamenti oggi", len(app_oggi), "📅")
    with col3:
        card_metrica("Richieste collegamento", len(richieste), "🔔",
                     colore="#E76F51" if richieste else "#B3A18D")
    with col4:
        card_metrica("Messaggi non letti", msg_non_letti, "💬",
                     colore="#E76F51" if msg_non_letti else "#B3A18D")

    divisore()

    # ── Richieste collegamento in attesa ──────────────────────────────────────
    if richieste:
        st.markdown("### 🔔 Richieste di collegamento in attesa")
        for r in richieste:
            owner = r.get("profiles") or {}
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{owner.get('nome','')} {owner.get('cognome','')}** — {owner.get('email','')}")
            with col2:
                if st.button("✅ Accetta", key=f"acc_{r['id']}", type="primary"):
                    from app.services.collegamenti_service import accetta_collegamento
                    accetta_collegamento(r["id"], vet_id)
                    st.success("Collegamento accettato!")
                    st.rerun()
            with col3:
                if st.button("❌ Rifiuta", key=f"rif_{r['id']}"):
                    from app.services.collegamenti_service import rifiuta_collegamento
                    rifiuta_collegamento(r["id"], vet_id)
                    st.rerun()
        divisore()

    # ── Agenda oggi ───────────────────────────────────────────────────────────
    st.markdown("### 📅 Agenda di oggi")
    if not app_oggi:
        empty_state("📅", "Nessun appuntamento per oggi", "Giornata libera! 🎉")
    else:
        for app in app_oggi:
            animale = app.get("animali") or {}
            owner = app.get("profiles") or {}
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(
                    f"**{format_datetime(app.get('data_ora'))}** — "
                    f"{icona_specie(animale.get('specie',''))} **{animale.get('nome','?')}**  \n"
                    f"👤 {owner.get('nome','')} {owner.get('cognome','')} · "
                    f"📝 {app.get('motivo','')}"
                )
            with col2:
                render_badge(app.get("stato", "in_attesa"))
            st.divider()

    # ── Ultime visite ─────────────────────────────────────────────────────────
    ultime_visite = get_ultime_visite_vet(vet_id, limite=5)
    if ultime_visite:
        st.markdown("### 📋 Ultime cartelle cliniche")
        for v in ultime_visite:
            animale = v.get("animali") or {}
            st.markdown(
                f"**{format_datetime(v.get('data_visita'))}** — "
                f"{icona_specie(animale.get('specie',''))} {animale.get('nome','?')} — "
                f"{v.get('diagnosi','')[:80]}…"
            )
