# pages/owner/veterinario.py
# Tabella vet disponibili, richiesta collegamento e recensioni.
import streamlit as st
import pandas as pd
from urllib.parse import quote
from app.auth.supabase_auth import get_current_profile
from app.services.collegamenti_service import (
    invia_richiesta_collegamento,
    get_collegamenti_owner, get_tutti_vet,
)
from app.services.listino_service import get_listino_owner
from app.services.recensioni_service import (
    get_recensioni_vet, get_media_voto, aggiungi_recensione,
    ha_gia_recensito, elimina_recensione,
)
from app.components.ui_helpers import render_badge, empty_state, divisore


def _stelle(voto: int) -> str:
    return "⭐" * voto + "☆" * (5 - voto)


def _sezione_recensioni(vet_id: str, owner_id: str, collegato: bool):
    recensioni = get_recensioni_vet(vet_id)
    media = get_media_voto(vet_id)

    if media is not None:
        st.markdown(
            f"<span style='font-size:1.1rem;font-weight:700;color:#B3A18D;'>"
            f"{'⭐' * round(media)} {media}/5</span> "
            f"<span style='color:#888;font-size:0.85rem;'>({len(recensioni)} recensioni)</span>",
            unsafe_allow_html=True,
        )
    else:
        st.caption("Nessuna recensione ancora.")

    # Form per lasciare una recensione (solo owner collegato)
    if collegato:
        gia_recensito = ha_gia_recensito(owner_id, vet_id)
        if gia_recensito:
            st.caption("Hai già lasciato una recensione per questo veterinario.")
            if st.button("🗑️ Elimina la mia recensione", key=f"del_rec_{vet_id}"):
                elimina_recensione(owner_id, vet_id)
                st.rerun()
        else:
            with st.expander("✏️ Lascia una recensione"):
                voto = st.select_slider(
                    "Voto",
                    options=[1, 2, 3, 4, 5],
                    value=5,
                    format_func=_stelle,
                    key=f"voto_{vet_id}",
                )
                testo = st.text_area("Commento (opzionale)", key=f"testo_rec_{vet_id}", height=80)
                if st.button("💾 Invia recensione", key=f"sub_rec_{vet_id}", type="primary"):
                    ok = aggiungi_recensione(owner_id, vet_id, voto, testo or None)
                    if ok:
                        st.success("Recensione inviata!")
                        st.rerun()
                    else:
                        st.error("Errore nell'invio.")

    # Lista recensioni
    if recensioni:
        for r in recensioni:
            autore = r.get("profiles") or {}
            nome_autore = f"{autore.get('nome','')} {autore.get('cognome','')}".strip() or "Proprietario"
            st.markdown(
                f'<div style="background:#F2EDE7;border-left:3px solid #B3A18D;'
                f'padding:0.6rem 1rem;border-radius:0 8px 8px 0;margin-bottom:0.4rem;">'
                f'<b>{_stelle(r["voto"])}</b> &nbsp; <span style="font-size:0.85rem;color:#555;">{nome_autore}</span><br>'
                f'<span style="font-size:0.9rem;">{r.get("testo") or ""}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


def show():
    profile = get_current_profile()
    owner_id = profile["id"]

    st.markdown("## 🩺 Il mio veterinario")

    collegamenti = get_collegamenti_owner(owner_id)
    id_accettati = {c["vet_id"] for c in collegamenti if c.get("stato") == "accepted"}
    id_collegati = {c["vet_id"] for c in collegamenti}

    # ── I miei collegamenti ───────────────────────────────────────────────────
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
                with st.expander("💶 Listino prezzi"):
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
        # Tabella con media voti
        df = pd.DataFrame([
            {
                "Veterinario": f"{v.get('nome','')} {v.get('cognome','')}",
                "Clinica":     v.get("clinica") or "—",
                "Telefono":    v.get("telefono") or "—",
                "Email":       v.get("email", ""),
                "Voto medio":  get_media_voto(v["id"]) or "—",
                "Stato":       "✅ Collegato" if v["id"] in id_collegati else "—",
            }
            for v in tutti_vet
        ])

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Veterinario": st.column_config.TextColumn("🩺 Veterinario"),
                "Clinica":     st.column_config.TextColumn("🏥 Clinica"),
                "Telefono":    st.column_config.TextColumn("📞 Telefono"),
                "Email":       st.column_config.TextColumn("📧 Email"),
                "Voto medio":  st.column_config.TextColumn("⭐ Voto medio"),
                "Stato":       st.column_config.TextColumn("Collegamento"),
            },
        )

        # Scheda espandibile per ogni vet: recensioni + collegamento
        for vet in tutti_vet:
            vet_id = vet["id"]
            media = get_media_voto(vet_id)
            media_str = f"⭐ {media}/5" if media else "Nessuna recensione"
            collegato = vet_id in id_accettati

            with st.expander(
                f"🩺 {vet.get('nome','')} {vet.get('cognome','')} "
                f"{'— ' + vet.get('clinica') if vet.get('clinica') else ''} · {media_str}"
            ):
                _sezione_recensioni(vet_id, owner_id, collegato)

                if vet_id not in id_collegati:
                    st.divider()
                    if st.button("🔗 Richiedi collegamento", key=f"col_{vet_id}", type="primary"):
                        ok = invia_richiesta_collegamento(owner_id, vet_id)
                        if ok:
                            st.success("Richiesta inviata!")
                            st.rerun()
                        else:
                            st.warning("Richiesta già inviata o errore.")

    divisore()

    # ── Il tuo veterinario non è registrato? ─────────────────────────────────
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
