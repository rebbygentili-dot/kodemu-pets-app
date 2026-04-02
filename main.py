"""
main.py
Entry point dell'applicazione VetBook.
Gestisce routing, autenticazione e navigazione per owner e vet.
"""
from app.pages.vet import chat as vet_chat
from app.pages.vet import listino as vet_listino
from app.pages.vet import agenda as vet_agenda
from app.pages.vet import cartella_clinica as vet_cartella
from app.pages.vet import pazienti as vet_pazienti
from app.pages.vet import dashboard as vet_dashboard
from app.pages.owner import chat as owner_chat
from app.pages.owner import veterinario as owner_veterinario
from app.pages.owner import documenti as owner_documenti
from app.pages.owner import appuntamenti as owner_appuntamenti
from app.pages.owner import vaccinazioni as owner_vaccinazioni
from app.pages.owner import animali as owner_animali
from app.pages.owner import dashboard as owner_dashboard
from app.pages import login as login_page
from app.auth.supabase_auth import is_logged_in, get_current_profile, get_ruolo, logout, completa_profilo
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Kodemu Pet",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Cancella lo stato sidebar salvato nel localStorage del browser
components.html(
    "<script>Object.keys(localStorage).forEach(k=>{ if(k.toLowerCase().includes('sidebar')) localStorage.removeItem(k); });</script>",
    height=0,
)

# ── Pagine Owner ──────────────────────────────────────────────────────────────

# ── Pagine Vet ────────────────────────────────────────────────────────────────

# ── CSS globale ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Sidebar compatta e fissa */
    [data-testid="stSidebar"] { min-width: 240px; max-width: 260px; }

    /* Nasconde i bottoni apri/chiudi sidebar */
    [data-testid="stSidebar"] [data-testid="stBaseButton-headerNoPadding"] { display: none !important; }
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }

    /* Bottoni primari */
    .stButton > button[kind="primary"] {
        background-color: #2D6A4F;
        border: none;
        color: #fff;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1B4332;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; }

    /* Expander */
    .streamlit-expanderHeader { font-weight: 600; }

    /* Nasconde footer e menu hamburger Streamlit */
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    header[data-testid="stHeader"] { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _pagina_completa_profilo(user_id: str):
    """Mostrata agli utenti invitati che non hanno ancora completato il profilo."""
    st.markdown(
        """
        <div style="text-align:center; padding: 2rem 0 1rem;">
            <div style="font-size:3.5rem;">🐾</div>
            <h1 style="font-size:2rem; font-weight:800; color:#2D6A4F; margin:0;">Benvenuto su Kodemu Pet!</h1>
            <p style="color:#666; margin-top:0.3rem;">Completa il tuo profilo per continuare.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ruolo = st.radio(
        "Sei un:",
        options=["owner", "vet"],
        format_func=lambda x: "🐾 Proprietario di animale" if x == "owner" else "🩺 Veterinario / Clinica",
        horizontal=True,
        key="completa_ruolo",
    )

    with st.form("form_completa_profilo"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome *")
        with col2:
            cognome = st.text_input("Cognome *")

        if st.session_state.get("completa_ruolo") == "vet":
            clinica = st.text_input("Nome clinica (opzionale)")
        else:
            clinica = ""

        submitted = st.form_submit_button("Salva e continua", use_container_width=True, type="primary")

    if submitted:
        if not nome or not cognome:
            st.warning("Nome e cognome sono obbligatori.")
        else:
            ok = completa_profilo(user_id, nome, cognome, ruolo, clinica or None)
            if ok:
                st.rerun()
            else:
                st.error("Errore nel salvataggio del profilo. Riprova.")


def _sidebar_owner(profile: dict):
    """Sidebar navigazione per il proprietario."""
    nome = profile.get("nome", "")
    st.sidebar.markdown(
        f"""
        <div style="text-align:center; padding:1rem 0 0.5rem;">
            <div style="font-size:2.5rem;">🐾</div>
            <div style="font-weight:800; font-size:1.2rem; color:#2D6A4F;">VetBook</div>
            <div style="font-size:0.8rem; color:#888; margin-top:2px;">👤 {nome}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.divider()

    pagine = {
        "🏠 Dashboard": "dashboard",
        "🐾 I miei animali": "animali",
        "💉 Vaccinazioni & Terapie": "vaccinazioni",
        "📅 Appuntamenti": "appuntamenti",
        "📁 Documenti": "documenti",
        "🩺 Il mio veterinario": "veterinario",
        "💬 Chat": "chat",
    }

    sel = st.sidebar.radio("Navigazione", list(
        pagine.keys()), label_visibility="collapsed")
    st.sidebar.divider()
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()

    return pagine[sel]


def _sidebar_vet(profile: dict):
    """Sidebar navigazione per il veterinario."""
    nome = profile.get("nome", "")
    cognome = profile.get("cognome", "")
    st.sidebar.markdown(
        f"""
        <div style="text-align:center; padding:1rem 0 0.5rem;">
            <div style="font-size:2.5rem;">🩺</div>
            <div style="font-weight:800; font-size:1.2rem; color:#1B4332;">VetBook Pro</div>
            <div style="font-size:0.8rem; color:#888; margin-top:2px;">Dr. {nome} {cognome}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.divider()

    pagine = {
        "🏠 Dashboard": "dashboard",
        "🐾 Pazienti": "pazienti",
        "📋 Cartelle Cliniche": "cartella",
        "📅 Agenda": "agenda",
        "💶 Listino prezzi": "listino",
        "💬 Chat": "chat",
    }

    sel = st.sidebar.radio("Navigazione", list(
        pagine.keys()), label_visibility="collapsed")
    st.sidebar.divider()
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()

    return pagine[sel]


# ── ROUTING PRINCIPALE ────────────────────────────────────────────────────────

if not is_logged_in():
    login_page.show()
else:
    profile = get_current_profile()

    # Profilo incompleto → utente invitato che non ha ancora completato la registrazione
    if not profile or not profile.get("nome"):
        user = st.session_state.get("user")
        _pagina_completa_profilo(user.id if user else "")
        st.stop()

    ruolo = get_ruolo()

    if ruolo == "owner":
        pagina = _sidebar_owner(profile)
        router_owner = {
            "dashboard":   owner_dashboard.show,
            "animali":     owner_animali.show,
            "vaccinazioni": owner_vaccinazioni.show,
            "appuntamenti": owner_appuntamenti.show,
            "documenti":   owner_documenti.show,
            "veterinario": owner_veterinario.show,
            "chat":        owner_chat.show,
        }
        router_owner.get(pagina, owner_dashboard.show)()

    elif ruolo == "vet":
        pagina = _sidebar_vet(profile)
        router_vet = {
            "dashboard": vet_dashboard.show,
            "pazienti":  vet_pazienti.show,
            "cartella":  vet_cartella.show,
            "agenda":    vet_agenda.show,
            "listino":   vet_listino.show,
            "chat":      vet_chat.show,
        }
        router_vet.get(pagina, vet_dashboard.show)()

    else:
        st.error("Ruolo non riconosciuto. Contatta il supporto.")
        if st.button("Logout"):
            logout()
            st.rerun()
