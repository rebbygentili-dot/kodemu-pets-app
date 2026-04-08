# main.py
# Entry point di Kodemu Pet. Gestisce il routing tra owner e vet, l'auth e i flow email (reset, invite).
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
from app.auth.supabase_auth import (
    is_logged_in, get_current_profile, get_ruolo, logout,
    completa_profilo, verifica_otp, aggiorna_password,
)
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Kodemu Pet",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Intercetta token Supabase dall'URL hash e li converte in query params leggibili da Streamlit
components.html(
    """
    <script>
    (function() {
        // Cancella stato sidebar
        Object.keys(localStorage).forEach(function(k) {
            if (k.toLowerCase().includes('sidebar')) localStorage.removeItem(k);
        });
        // Rileva token auth di Supabase nel hash dell'URL (es. #access_token=...&type=recovery)
        var hash = window.parent.location.hash;
        if (hash && hash.includes('access_token')) {
            var params = new URLSearchParams(hash.substring(1));
            var accessToken  = params.get('access_token')  || '';
            var refreshToken = params.get('refresh_token') || '';
            var type         = params.get('type')          || '';
            if (accessToken) {
                window.parent.location.href =
                    window.parent.location.pathname +
                    '?access_token='  + encodeURIComponent(accessToken)  +
                    '&refresh_token=' + encodeURIComponent(refreshToken) +
                    '&type='          + encodeURIComponent(type);
            }
        }
    })();
    </script>
    """,
    height=0,
)

# ── Pagine Owner ──────────────────────────────────────────────────────────────

# ── Pagine Vet ────────────────────────────────────────────────────────────────

# ── CSS globale ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Sidebar compatta e fissa */
    [data-testid="stSidebar"] { min-width: 240px; max-width: 260px; background-color: #bda18d94; }

    /* Nasconde i bottoni apri/chiudi sidebar */
    [data-testid="stSidebar"] [data-testid="stBaseButton-headerNoPadding"] { display: none !important; }
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }

    /* Tutti i bottoni */
    .stButton > button, .stFormSubmitButton > button {
        background-color: #B3A18D !important;
        border: none !important;
        color: #fff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        background-color: #8A7A6A !important;
        color: #fff !important;
    }

    /* Tabs — linea attiva e testo */
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #B3A18D !important; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: #B3A18D !important; }

    /* Input — bordo sempre e al focus */
    [data-baseweb="input"] > div,
    [data-baseweb="textarea"] > div,
    [data-baseweb="base-input"],
    [data-testid="stTextInput"] > div > div,
    [data-testid="stTextArea"] > div > div {
        border-color: #C9B8A6 !important;
    }
    [data-baseweb="input"]:focus-within > div,
    [data-baseweb="textarea"]:focus-within > div,
    [data-testid="stTextInput"] > div > div:focus-within,
    [data-testid="stTextArea"] > div > div:focus-within {
        border-color: #B3A18D !important;
        box-shadow: 0 0 0 1px #B3A18D !important;
    }

    /* Selectbox — bordo sempre e al focus */
    [data-baseweb="select"] > div {
        border-color: #C9B8A6 !important;
    }
    [data-baseweb="select"] > div:focus-within {
        border-color: #B3A18D !important;
        box-shadow: 0 0 0 1px #B3A18D !important;
    }

    /* Checkbox e radio — colore accent */
    input[type="radio"]:checked, input[type="checkbox"]:checked {
        accent-color: #B3A18D !important;
    }

    /* Hover menu a tendina (selectbox, multiselect) */
    [data-baseweb="option"]:hover,
    [data-baseweb="menu"] li:hover,
    [role="option"]:hover {
        background-color: #bda18d94 !important;
    }

    /* Voce selezionata nei menu a tendina */
    [aria-selected="true"][data-baseweb="option"],
    [role="option"][aria-selected="true"] {
        background-color: #bda18d94 !important;
    }

    /* Radio button selezionato (navigazione sidebar) */
    [data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div,
    [data-testid="stSidebar"] [role="radio"][aria-checked="true"] {
        border-color: #B3A18D !important;
        background-color: #bda18d94 !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
        background-color: #bda18d94 !important;
        border-radius: 6px;
    }

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


def _pagina_reset_password(token_hash: str):
    """Pagina per impostare una nuova password via link di recovery."""
    st.markdown(
        """
        <div style="text-align:center; padding: 2rem 0 1rem;">
            <div style="font-size:3.5rem;">🔑</div>
            <h1 style="font-size:2rem; font-weight:800; color:#B3A18D; margin:0;">Imposta nuova password</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("form_reset_pwd"):
        nuova_pwd    = st.text_input("Nuova password *", type="password", help="Minimo 8 caratteri")
        conferma_pwd = st.text_input("Conferma password *", type="password")
        submitted    = st.form_submit_button("Salva password", type="primary", use_container_width=True)

    if submitted:
        if not nuova_pwd or not conferma_pwd:
            st.warning("Compila entrambi i campi.")
        elif nuova_pwd != conferma_pwd:
            st.error("Le password non coincidono.")
        elif len(nuova_pwd) < 8:
            st.error("La password deve avere almeno 8 caratteri.")
        else:
            ok_session = verifica_otp(token_hash, "recovery")
            if ok_session:
                ok_pwd = aggiorna_password(nuova_pwd)
                if ok_pwd:
                    # Logout dalla sessione recovery e rimanda al login con messaggio
                    logout()
                    st.session_state["flash_success"] = "✅ Password aggiornata! Accedi con la tua nuova password."
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error("Errore nell'aggiornamento della password. Riprova.")
            else:
                st.error("Link scaduto o non valido. Richiedine uno nuovo dalla pagina di login.")


def _pagina_completa_profilo(user_id: str):
    """Mostrata agli utenti invitati che non hanno ancora completato il profilo."""
    st.markdown(
        """
        <div style="text-align:center; padding: 2rem 0 1rem;">
            <div style="font-size:3.5rem;">🐾</div>
            <h1 style="font-size:2rem; font-weight:800; color:#B3A18D; margin:0;">Benvenuto su Kodemu Pet!</h1>
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
            <div style="font-weight:800; font-size:1.2rem; color:#fff;">Kodemu Pet</div>
            <div style="font-size:0.8rem; color:#fff; margin-top:2px;">👤 {nome}</div>
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
            <div style="font-weight:800; font-size:1.2rem; color:#fff;">Kodemu Vet</div>
            <div style="font-size:0.8rem; color:#fff; margin-top:2px;">Dr. {nome} {cognome}</div>
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

# ── Gestione token auth da URL (recovery / invite) ───────────────────────────
_qp = st.query_params
if "token_hash" in _qp:
    _token_hash = _qp.get("token_hash", "")
    _token_type = _qp.get("type", "")

    if _token_type == "recovery":
        _pagina_reset_password(_token_hash)
        st.stop()
    elif _token_type in ("invite", "magiclink", "signup", "email"):
        ok = verifica_otp(_token_hash, _token_type)
        if ok:
            st.query_params.clear()
            st.session_state["flash_success"] = "✅ Email confermata! Sei ora loggato."
            st.rerun()
        else:
            st.error("Link non valido o scaduto. Torna alla pagina di login.")
            st.stop()

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
