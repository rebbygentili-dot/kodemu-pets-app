# pages/owner/animali.py
# Gestione animali del proprietario: lista, aggiunta, modifica, eliminazione.
import streamlit as st
from datetime import date
from app.auth.supabase_auth import get_current_profile
from app.services.animali_service import (
    get_animali_by_owner, crea_animale, aggiorna_animale, elimina_animale,
    SPECIE, get_suggerimenti,
)
from app.services.collegamenti_service import get_vet_collegati_owner
from app.components.ui_helpers import icona_specie, format_data, empty_state, divisore


def show():
    profile = get_current_profile()
    owner_id = profile["id"]

    st.markdown("## 🐾 I miei animali")

    # Pulsante per aggiungere
    if st.button("➕ Aggiungi animale", type="primary"):
        st.session_state["animale_form_aperto"] = True
        st.session_state["animale_in_modifica"] = None

    # ── Form aggiunta / modifica ───────────────────────────────────────────────
    if st.session_state.get("animale_form_aperto"):
        _form_animale(owner_id)
        st.divider()

    # ── Lista animali ─────────────────────────────────────────────────────────
    animali = get_animali_by_owner(owner_id)

    if not animali:
        empty_state("🐾", "Nessun animale ancora",
                    "Aggiungi il tuo primo animale cliccando il pulsante sopra.")
        return

    for animale in animali:
        _card_animale(animale, owner_id)


def _card_animale(animale: dict, owner_id: str):
    specie = animale.get("specie", "")
    with st.expander(f"{icona_specie(specie)} **{animale['nome']}** — {specie} · {animale.get('razza','')}", expanded=False):
        col_info, col_azioni = st.columns([3, 1])

        with col_info:
            st.markdown(
                f"**Data di nascita:** {format_data(animale.get('data_nascita'))}")
            st.markdown(f"**Microchip:** {animale.get('microchip') or '—'}")
            st.markdown(f"**Peso:** {animale.get('peso_kg') or '—'} kg")
            vet_profile = animale.get("profiles") or {}
            # nella card di ogni animale viene mostrata la riga "Veterinario di riferimento"
            if vet_profile:
                vet_nome = f"🩺 {vet_profile.get('nome', '')} {vet_profile.get('cognome', '')}".strip(
                )
                if vet_profile.get("clinica"):
                    vet_nome += f" — {vet_profile['clinica']}"
                st.markdown(f"**Veterinario di riferimento:** {vet_nome}")
            else:
                st.markdown("**Veterinario di riferimento:** —")
            if animale.get("allergie"):
                st.markdown(f"**Allergie:** {animale['allergie']}")
            if animale.get("note"):
                st.markdown(f"**Note:** {animale['note']}")

            # Suggerimenti specie-specifici
            suggerimenti = get_suggerimenti(specie)
            if suggerimenti:
                divisore("💡 Suggerimenti")
                for s in suggerimenti:
                    st.info(s)

        with col_azioni:
            if st.button("✏️ Modifica", key=f"mod_{animale['id']}"):
                st.session_state["animale_form_aperto"] = True
                st.session_state["animale_in_modifica"] = animale
                st.rerun()
            if st.button("🗑️ Elimina", key=f"del_{animale['id']}"):
                st.session_state[f"confirm_del_{animale['id']}"] = True

        if st.session_state.get(f"confirm_del_{animale['id']}"):
            st.warning(
                f"Sei sicuro di voler eliminare **{animale['nome']}**? Questa operazione è irreversibile.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Sì, elimina", key=f"yes_{animale['id']}", type="primary"):
                    elimina_animale(animale["id"])
                    st.success("Animale eliminato.")
                    st.session_state.pop(f"confirm_del_{animale['id']}", None)
                    st.rerun()
            with c2:
                if st.button("❌ Annulla", key=f"no_{animale['id']}"):
                    st.session_state.pop(f"confirm_del_{animale['id']}", None)
                    st.rerun()


def _form_animale(owner_id: str):
    editing = st.session_state.get("animale_in_modifica")
    # Carica vet collegati per il selettore (fuori dal form)
    vet_collegati = get_vet_collegati_owner(owner_id)
    titolo = "✏️ Modifica animale" if editing else "➕ Nuovo animale"

    st.markdown(f"### {titolo}")

    with st.form("form_animale"):
        specie = st.selectbox(
            "Specie *",
            SPECIE,
            format_func=lambda s: f"{icona_specie(s)} {s}",
            index=SPECIE.index(editing["specie"]) if editing else 0,
        )

        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input(
                "Nome *", value=editing.get("nome", "") if editing else "")
            data_nascita = st.date_input(
                "Data di nascita",
                value=date.fromisoformat(editing["data_nascita"]) if editing and editing.get(
                    "data_nascita") else date(2020, 1, 1),
                max_value=date.today(),
            )
        with col2:
            razza = st.text_input("Razza", value=editing.get("razza", "") if editing else "",
                                  placeholder="es. Labrador / Meticcio")
            microchip = st.text_input("N. Microchip", value=editing.get("microchip", "") if editing else "",
                                      placeholder="Lascia vuoto se assente", help="Il microchip è un codice numerico univoco a 15 cifre. Lascia vuoto se l'animale non è ancora microchippato.")

        col3, col4 = st.columns(2)
        with col3:
            peso = st.number_input("Peso (kg)", min_value=0.0, max_value=999.0, step=0.1,
                                   value=float(editing.get("peso_kg") or 0) if editing else 0.0)
        with col4:
            _opzioni_sesso = ["Maschio intero", "Maschio castrato",
                              "Femmina intera", "Femmina sterilizzata", "Non specificato"]
            _sesso_default = editing.get(
                "sesso", "Non specificato") if editing else "Non specificato"
            if _sesso_default not in _opzioni_sesso:
                _sesso_default = "Non specificato"
            sesso = st.selectbox("Sesso", _opzioni_sesso,
                                 index=_opzioni_sesso.index(_sesso_default))

        # Selettore veterinario di riferimento
        vet_id_sel = None
        if vet_collegati:
            nessuno = {"vet_id": None, "profiles": {
                "nome": "—", "cognome": "", "clinica": ""}}
            opzioni_vet = [nessuno] + vet_collegati

            def _label_vet(v):
                p = v.get("profiles") or {}
                label = f"🩺 {p.get('nome','')} {p.get('cognome','')}".strip()
                if p.get("clinica"):
                    label += f" — {p['clinica']}"
                return label if v["vet_id"] else "— Nessun vet assegnato"

            # Indice default: trova il vet già assegnato se in modifica
            idx_default = 0
            if editing and editing.get("vet_id"):
                for i, v in enumerate(opzioni_vet):
                    if v["vet_id"] == editing["vet_id"]:
                        idx_default = i
                        break

            sel_vet = st.selectbox(
                "Veterinario di riferimento",
                options=opzioni_vet,
                format_func=_label_vet,
                index=idx_default,
                key="sel_vet_animale",
            )
            vet_id_sel = sel_vet["vet_id"]

        # Campi specie-specifici
        sterilizzato = None
        interno_esterno = None
        passaporto_equino = None
        scuderia = None

        if specie == "Gatto":
            col5, col6 = st.columns(2)
            with col5:
                sterilizzato = st.radio("Sterilizzato?", ["Sì", "No"], horizontal=True,
                                        index=0 if (editing and editing.get("sterilizzato")) else 1)
            with col6:
                interno_esterno = st.selectbox("Tipo", ["Solo interno", "Solo esterno", "Misto"],
                                               index=0)
        elif specie == "Cavallo":
            col5, col6 = st.columns(2)
            with col5:
                passaporto_equino = st.text_input("N. Passaporto equino",
                                                  value=editing.get("passaporto_equino", "") if editing else "")
            with col6:
                scuderia = st.text_input("Scuderia", value=editing.get(
                    "scuderia", "") if editing else "")

        allergie = st.text_area("Allergie note", value=editing.get("allergie", "") if editing else "",
                                height=80)
        note = st.text_area("Note aggiuntive", value=editing.get("note", "") if editing else "",
                            height=80)

        col_sub, col_ann = st.columns(2)
        with col_sub:
            submitted = st.form_submit_button(
                "💾 Salva", type="primary", use_container_width=True)
        with col_ann:
            annulla = st.form_submit_button(
                "❌ Annulla", use_container_width=True)

    if annulla:
        st.session_state["animale_form_aperto"] = False
        st.session_state["animale_in_modifica"] = None
        st.rerun()

    if submitted:
        if not nome:
            st.error("Il nome è obbligatorio.")
            return

        payload = {
            "owner_id": owner_id,
            "vet_id": vet_id_sel,
            "specie": specie,
            "nome": nome.strip().title(),
            "razza": razza.strip().title() if razza else None,
            "data_nascita": data_nascita.isoformat(),
            "microchip": microchip or None,
            "peso_kg": peso or None,
            "sesso": sesso,
            "allergie": allergie or None,
            "note": note or None,
        }
        if specie == "Gatto":
            payload["sterilizzato"] = sterilizzato == "Sì"
            payload["interno_esterno"] = interno_esterno
        elif specie == "Cavallo":
            payload["passaporto_equino"] = passaporto_equino or None
            payload["scuderia"] = scuderia or None

        if editing:
            ok = aggiorna_animale(editing["id"], payload)
            msg = "Animale aggiornato!"
        else:
            try:
                ok = crea_animale(payload)
                msg = "Animale aggiunto!"
            except Exception as e:
                if "animali_microchip_key" in str(e):
                    st.error(
                        "Il numero di microchip è già registrato per un altro animale.")
                else:
                    st.error(f"Errore nel salvataggio: {e}")
                ok = None
                msg = ""

        if ok:
            st.success(msg)
            st.session_state["animale_form_aperto"] = False
            st.session_state["animale_in_modifica"] = None
            st.rerun()
        elif ok is not None:
            st.error("Errore nel salvataggio.")
