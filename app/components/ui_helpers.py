# components/ui_helpers.py
# Helper UI condivisi: badge stato, icone specie, formati data, card metriche, empty state.
import streamlit as st
from datetime import date, datetime


# ── Metriche colorate ─────────────────────────────────────────────────────────

def card_metrica(titolo: str, valore: str | int, icona: str = "", colore: str = "#B3A18D"):
    st.markdown(
        f"""
        <div style="background:{colore}18; border-left:4px solid {colore};
                    padding:1rem 1.2rem; border-radius:8px; margin-bottom:0.5rem;">
            <div style="font-size:0.8rem; color:#555; text-transform:uppercase; letter-spacing:0.05em;">{icona} {titolo}</div>
            <div style="font-size:1.8rem; font-weight:700; color:{colore};">{valore}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Badge stato ───────────────────────────────────────────────────────────────

BADGE_COLORS = {
    "pending":    ("#FFF3CD", "#856404"),
    "accepted":   ("#D1E7DD", "#0F5132"),
    "rejected":   ("#F8D7DA", "#842029"),
    "in_attesa":  ("#FFF3CD", "#856404"),
    "confermato": ("#D1E7DD", "#0F5132"),
    "completato": ("#CFE2FF", "#084298"),
    "annullato":  ("#F8D7DA", "#842029"),
}

BADGE_LABEL = {
    "pending":    "⏳ In attesa",
    "accepted":   "✅ Accettato",
    "rejected":   "❌ Rifiutato",
    "in_attesa":  "⏳ In attesa",
    "confermato": "✅ Confermato",
    "completato": "🏁 Completato",
    "annullato":  "❌ Annullato",
}


def badge_stato(stato: str) -> str:
    bg, fg = BADGE_COLORS.get(stato, ("#e0e0e0", "#333"))
    label = BADGE_LABEL.get(stato, stato)
    return f'<span style="background:{bg}; color:{fg}; padding:2px 10px; border-radius:20px; font-size:0.82rem; font-weight:600;">{label}</span>'


def render_badge(stato: str):
    st.markdown(badge_stato(stato), unsafe_allow_html=True)


# ── Divisore elegante ─────────────────────────────────────────────────────────

def divisore(testo: str = ""):
    if testo:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:0.8rem;margin:1rem 0;">'
            f'<hr style="flex:1;border:none;border-top:1px solid #ddd;">'
            f'<span style="color:#888;font-size:0.85rem;white-space:nowrap;">{testo}</span>'
            f'<hr style="flex:1;border:none;border-top:1px solid #ddd;"></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<hr style='border:none;border-top:1px solid #ddd;margin:1rem 0;'>", unsafe_allow_html=True)


# ── Icona specie ──────────────────────────────────────────────────────────────

ICONE_SPECIE = {"Cane": "🐶", "Gatto": "🐱", "Cavallo": "🐴"}


def icona_specie(specie: str) -> str:
    return ICONE_SPECIE.get(specie, "🐾")


# ── Formato data ──────────────────────────────────────────────────────────────

def format_data(d) -> str:
    if not d:
        return "—"
    if isinstance(d, str):
        try:
            d = datetime.fromisoformat(d)
        except Exception:
            return d
    return d.strftime("%d/%m/%Y")


def format_datetime(d) -> str:
    if not d:
        return "—"
    if isinstance(d, str):
        try:
            d = datetime.fromisoformat(d)
        except Exception:
            return d
    return d.strftime("%d/%m/%Y %H:%M")


# ── Messaggio vuoto ────────────────────────────────────────────────────────────

def empty_state(icona: str, titolo: str, descrizione: str = ""):
    st.markdown(
        f"""
        <div style="text-align:center; padding:3rem 1rem; color:#888;">
            <div style="font-size:3rem;">{icona}</div>
            <div style="font-size:1.1rem; font-weight:600; margin-top:0.5rem;">{titolo}</div>
            {"<div style='font-size:0.9rem; margin-top:0.3rem;'>" + descrizione + "</div>" if descrizione else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )
