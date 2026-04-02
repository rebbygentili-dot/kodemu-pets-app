"""
pages/owner/veterinario.py
Gestione collegamento con il veterinario.
"""
import streamlit as st
import pandas as pd
from urllib.parse import quote
from app.auth.supabase_auth import get_current_profile
from app.services.collegamenti_service import (
    invia_richiesta_collegamento,
    get_collegamenti_owner, get_tutti_vet,
)
from app.services.listino_service import get_listino_owner
from app.components.ui_helpers import render_badge, empty_state, divisore


def show():
    profile = get_current_profile()
    owner_id = profile["id"]

    st.markdown("## 🩺 Il mio veterinario")

    # ── Collegamenti esistenti ────────────────────────────────────────────────
    collegamenti = get_collegamenti_owner(owner_id)
    if collegamenti:
        st.markdown("### 🔗 I tuoi collegamenti")
        for col in collegamenti:
            vet_profile = col.get("profiles") or {}
            stato = col.get("stato", "pending")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(
                    f"**🩺 {vet_profile.get('nome','')} {vet_profile.get('cognome','')}**  \n"
                    f"{vet_profile.get('clinica') or ''} · {vet_profile.get('email','')}",
                )
            with col2:
                render_badge(stato)
            if stato == "accepted":
                with st.expander("💶 Vedi listino prezzi"):
                    voci = get_listino_owner(col["vet_id"])
                    if not voci:
                        st.caption("Il veterinario non ha ancora pubblicato un listino.")
                    else:
                        categorie: dict = {}
                        for v in voci:
                            categorie.setdefault(v.get("categoria", "Altro"), []).append(v)
                        for cat, items in sorted(categorie.items()):
                            st.markdown(f"**{cat}**")
                            for v in items:
                                r1, r2 = st.columns([3, 1])
                                with r1:
                                    durata = f" · {v['durata_minuti']} min" if v.get("durata_minuti") else ""
                                    disp = v.get("disponibilita", "")
                                    st.markdown(
                                        f"{v.get('nome_prestazione','')}  \n"
                                        f"<span style='font-size:0.8rem;color:#888;'>{disp}{durata}</span>",
                                        unsafe_allow_html=True,
                                    )
                                    if v.get("note"):
                                        st.caption(v["note"])
                                with r2:
                                    st.markdown(f"**€ {v.get('prezzo', 0):.2f}**")
        divisore()

    # ── Tutti i veterinari disponibili ───────────────────────────────────────
    st.markdown("### 🏥 Veterinari disponibili sulla piattaforma")

    tutti_vet = get_tutti_vet()
    if not tutti_vet:
        empty_state("🩺", "Nessun veterinario registrato", "Non ci sono ancora veterinari sulla piattaforma.")
    else:
        id_collegati = {c["vet_id"] for c in collegamenti}

        # Tabella pandas
        df = pd.DataFrame([
            {
                "Nome":     f"{v.get('nome','')} {v.get('cognome','')}",
                "Clinica":  v.get("clinica") or "—",
                "Telefono": v.get("telefono") or "—",
                "Email":    v.get("email", ""),
                "Stato":    "✅ Collegato" if v["id"] in id_collegati else "—",
            }
            for v in tutti_vet
        ])

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Nome":     st.column_config.TextColumn("🩺 Veterinario"),
                "Clinica":  st.column_config.TextColumn("🏥 Clinica"),
                "Telefono": st.column_config.TextColumn("📞 Telefono"),
                "Email":    st.column_config.TextColumn("📧 Email"),
                "Stato":    st.column_config.TextColumn("Collegamento"),
            },
        )

        # Bottoni collegamento per vet non ancora collegati
        non_collegati = [v for v in tutti_vet if v["id"] not in id_collegati]
        if non_collegati:
            divisore("🔗 Richiedi collegamento")
            for vet in non_collegati:
                vet_id = vet["id"]
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(
                        f"**{vet.get('nome','')} {vet.get('cognome','')}**"
                        f"{' — ' + vet.get('clinica') if vet.get('clinica') else ''}"
                    )
                with col2:
                    if st.button("🔗 Collega", key=f"col_{vet_id}", use_container_width=True):
                        ok = invia_richiesta_collegamento(owner_id, vet_id)
                        if ok:
                            st.success("Richiesta inviata!")
                            st.rerun()
                        else:
                            st.warning("Richiesta già inviata o errore.")

    divisore()

    # ── Il tuo veterinario non è registrato? ────────────────────────────────
    st.markdown("### 📧 Il tuo veterinario non è ancora registrato?")
    email_invito = st.text_input("Email del veterinario", placeholder="vet@clinica.it", key="email_invito")

    if email_invito:
        oggetto = quote("Ti invito su Kodemu Pet")
        corpo = quote(
            "Ciao,\n\nti invito a registrarti su Kodemu Pet, la piattaforma digitale per la gestione "
            "della salute dei tuoi pazienti.\n\nRegistrati qui: https://kodemu.it\n\nA presto!"
        )
        mailto = f"mailto:{email_invito}?subject={oggetto}&body={corpo}"
        st.link_button("📧 Apri email e invia invito", mailto, use_container_width=True, type="primary")
