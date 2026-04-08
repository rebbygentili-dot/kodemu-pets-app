# pages/login.py
# Login e registrazione in un'unica pagina con tab.
import streamlit as st
from app.auth.supabase_auth import login, register, richiedi_reset_password


def show():
    st.markdown(
        """
        <div style="text-align:center; padding: 2rem 0 1rem;">
            <div style="font-size:3.5rem;">🐾</div>
            <h1 style="font-size:2.2rem; font-weight:800; color:#B3A18D; margin:0;">Kodemu Pet</h1>
            <p style="color:#666; margin-top:0.3rem;">Il fascicolo sanitario digitale per il tuo animale</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Messaggio di successo dopo reset password
    if st.session_state.get("flash_success"):
        st.success(st.session_state.pop("flash_success"))

    tab_login, tab_register = st.tabs(["🔑 Accedi", "📝 Registrati"])

    # ── TAB LOGIN ─────────────────────────────────────────────────────────────
    with tab_login:
        with st.form("form_login"):
            email = st.text_input("Email", placeholder="tuamail@esempio.it")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Accedi", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                st.warning("Inserisci email e password.")
            else:
                with st.spinner("Accesso in corso..."):
                    user = login(email, password)
                if user:
                    st.success("Accesso effettuato!")
                    st.rerun()
                else:
                    st.error("Credenziali non valide. Riprova.")

        # ── Password dimenticata ───────────────────────────────────────────────
        with st.expander("🔑 Hai dimenticato la password?"):
            email_reset = st.text_input(
                "Inserisci la tua email", placeholder="tuamail@esempio.it", key="email_reset"
            )
            if st.button("📧 Invia link di reset", use_container_width=True, type="primary"):
                if not email_reset:
                    st.warning("Inserisci l'email.")
                else:
                    ok = richiedi_reset_password(email_reset)
                    if ok:
                        st.success("✅ Email inviata! Controlla la casella e clicca il link.")
                    else:
                        st.error("Errore nell'invio. Verifica l'indirizzo email.")

    # ── TAB REGISTRAZIONE ─────────────────────────────────────────────────────
    with tab_register:
        # La radio è FUORI dal form per consentire il re-render dinamico
        ruolo = st.radio(
            "Sei un:",
            options=["owner", "vet"],
            format_func=lambda x: "🐾 Proprietario di animale" if x == "owner" else "🩺 Veterinario / Clinica",
            horizontal=True,
            key="reg_ruolo",
        )

        with st.form("form_register"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome *")
            with col2:
                cognome = st.text_input("Cognome *")

            email_r = st.text_input(
                "Email *", placeholder="tuamail@esempio.it", key="reg_email")
            password_r = st.text_input("Password *", type="password", key="reg_pwd",
                                       help="Minimo 8 caratteri")
            password_confirm = st.text_input(
                "Conferma password *", type="password")

            if ruolo == "vet":
                clinica = st.text_input("Nome clinica (opzionale)")
            else:
                clinica = ""

            submitted_r = st.form_submit_button(
                "Registrati", use_container_width=True, type="primary")

        if submitted_r:
            clinica_val = clinica if ruolo == "vet" else ""
            if not all([nome, cognome, email_r, password_r]):
                st.warning("Compila tutti i campi obbligatori.")
            elif password_r != password_confirm:
                st.error("Le password non coincidono.")
            elif len(password_r) < 8:
                st.error("La password deve avere almeno 8 caratteri.")
            else:
                with st.spinner("Creazione account..."):
                    ok = register(email_r, password_r, nome, cognome, ruolo)
                if ok:
                    st.success(
                        "✅ Registrazione completata! Controlla la tua email per confermare l'account, poi accedi.")
                else:
                    st.error(
                        "Errore durante la registrazione. L'email potrebbe essere già in uso.")
