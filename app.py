import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime, time
import math

st.set_page_config(page_title="OEE Spray Dryer", layout="wide")

st.markdown("""
<style>
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background-color: #2E7D32 !important;
    color: white !important;
    border: 1px solid #2E7D32 !important;
    font-weight: 700 !important;
}
.stButton > button[kind="secondary"],
.stFormSubmitButton > button[kind="secondary"] {
    border: 1px solid #757575 !important;
    font-weight: 600 !important;
}
.alert-standby {
    background-color: #FFF3CD;
    border-left: 6px solid #FF9800;
    padding: 12px 16px;
    border-radius: 6px;
    color: #4E342E;
    font-weight: 600;
}
.alert-ok {
    background-color: #E8F5E9;
    border-left: 6px solid #2E7D32;
    padding: 12px 16px;
    border-radius: 6px;
    color: #1B5E20;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# =========================
# CONFIGURAZIONE
# =========================

ADMIN_PASSWORD = "EVRA26%"

TURNI = {
    "1": {"inizio": time(6, 0), "fine": time(14, 0)},
    "2": {"inizio": time(14, 0), "fine": time(22, 0)},
    "3": {"inizio": time(22, 0), "fine": time(6, 0)},
}

TURNO_H = 8

TIPI_EVENTO = [
    "Produzione",
    "Attesa prodotto",
    "Attesa analisi",
    "Cambio lotto",
    "Lavaggio",
    "Guasto",
    "Manutenzione programmata",
    "Manutenzione straordinaria",
    "Pulizia",
    "Altro",
]

CAUSALI_TECNICHE = ["Guasto", "Manutenzione straordinaria"]

CAUSE_NC = [
    "Titolo insufficiente",
    "Umidità alta",
    "Umidità bassa",
    "Granulometria fuori specifica",
    "Densità apparente",
    "Colore",
    "Odore",
    "Microbiologia",
    "Residui solventi",
    "Corpo estraneo",
    "Errore documentale",
    "Altro",
]

PRODOTTI_FILE = Path("data/prodotti.csv")
PRODUZIONI_FILE = Path("data/produzioni.csv")
FERMI_FILE = Path("data/fermi.csv")

COL_PRODOTTI = ["codice_prodotto", "descrizione_prodotto", "capacita_kg_h"]

COL_PRODUZIONI = [
    "id_lotto",
    "id_turno",
    "data",
    "turno",
    "codice_prodotto",
    "descrizione_prodotto",
    "lotto",
    "kg_molle",
    "residuo_secco",
    "kg_polvere_teorica",
    "kg_polvere_reale",
    "ora_inizio",
    "ora_fine",
    "ore_produzione",
    "stato_analisi",
    "kg_conformi",
    "kg_nc",
    "causa_nc",
    "note_nc",
    "data_rilascio_analisi",
]

COL_FERMI = [
    "id_fermo",
    "id_turno",
    "data",
    "turno",
    "ora_inizio",
    "ora_fine",
    "durata_h",
    "causale_fermo",
    "note_fermo",
]


# =========================
# FUNZIONI BASE
# =========================

def inizializza_file():
    Path("data").mkdir(parents=True, exist_ok=True)

    if not PRODOTTI_FILE.exists():
        pd.DataFrame(columns=COL_PRODOTTI).to_csv(PRODOTTI_FILE, index=False)

    if not PRODUZIONI_FILE.exists():
        pd.DataFrame(columns=COL_PRODUZIONI).to_csv(PRODUZIONI_FILE, index=False)

    if not FERMI_FILE.exists():
        pd.DataFrame(columns=COL_FERMI).to_csv(FERMI_FILE, index=False)


def leggi_csv(path, colonne):
    inizializza_file()
    df = pd.read_csv(path, dtype=str)

    for col in colonne:
        if col not in df.columns:
            df[col] = ""

    return df[colonne]


def salva_csv(df, path, colonne):
    for col in colonne:
        if col not in df.columns:
            df[col] = ""
    df[colonne].to_csv(path, index=False)


def assegna_valore(df, mask, colonna, valore):
    """Assegna valori in modo robusto evitando errori dtype su Streamlit/Pandas."""
    if colonna not in df.columns:
        df[colonna] = ""
    df[colonna] = df[colonna].astype("object")
    df.loc[mask, colonna] = str(valore)
    return df


def leggi_prodotti():
    df = leggi_csv(PRODOTTI_FILE, COL_PRODOTTI)

    if df.empty:
        df = pd.DataFrame([{
            "codice_prodotto": "INSERIRE",
            "descrizione_prodotto": "Inserire anagrafica prodotti",
            "capacita_kg_h": "20",
        }])

    df["capacita_kg_h"] = pd.to_numeric(df["capacita_kg_h"], errors="coerce").fillna(20)
    return df


def leggi_produzioni():
    return leggi_csv(PRODUZIONI_FILE, COL_PRODUZIONI)


def leggi_fermi():
    return leggi_csv(FERMI_FILE, COL_FERMI)


def safe_float(value, default=0.0):
    val = pd.to_numeric(value, errors="coerce")
    if pd.isna(val):
        return default
    return float(val)


def safe_div(num, den):
    if den is None or den == 0 or pd.isna(den):
        return 0
    return num / den


def ore_da_orari(ora_inizio, ora_fine):
    if ora_inizio is None or ora_fine is None:
        return 0

    try:
        dt_i = datetime.combine(datetime.today(), ora_inizio)
        dt_f = datetime.combine(datetime.today(), ora_fine)
        durata = (dt_f - dt_i).total_seconds() / 3600

        if durata < 0:
            durata += 24

        return durata
    except Exception:
        return 0


def parse_time_str(value, fallback):
    try:
        if value in [None, "", "nan"]:
            return fallback
        return datetime.strptime(str(value)[:8], "%H:%M:%S").time()
    except Exception:
        try:
            return datetime.strptime(str(value)[:5], "%H:%M").time()
        except Exception:
            return fallback


def prepara_produzioni(df):
    if df.empty:
        return df

    for col in [
        "kg_molle",
        "residuo_secco",
        "kg_polvere_teorica",
        "kg_polvere_reale",
        "ore_produzione",
        "kg_conformi",
        "kg_nc",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["kg_polvere_teorica"] = df["kg_molle"] * df["residuo_secco"] / 100
    df["resa"] = df.apply(lambda r: safe_div(r["kg_polvere_reale"], r["kg_polvere_teorica"]), axis=1)

    return df


def prepara_fermi(df):
    if df.empty:
        return df

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["durata_h"] = pd.to_numeric(df["durata_h"], errors="coerce").fillna(0)

    return df


def reset_eventi_turno():
    st.session_state["eventi_turno"] = []
    st.session_state["evento_da_modificare"] = None


def nuovo_id():
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


def gauge_oee(valore):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valore * 100,
        number={"suffix": "%", "font": {"size": 42}},
        title={"text": "OEE Spray Dryer", "font": {"size": 24}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"thickness": 0.28},
            "steps": [
                {"range": [0, 50], "color": "#ff4b4b"},
                {"range": [50, 65], "color": "#ffa500"},
                {"range": [65, 75], "color": "#ffd966"},
                {"range": [75, 85], "color": "#9be564"},
                {"range": [85, 100], "color": "#2ecc71"},
            ],
            "threshold": {"line": {"color": "black", "width": 4}, "thickness": 0.75, "value": 75},
        },
    ))
    fig.update_layout(height=330, margin=dict(l=30, r=30, t=70, b=20))
    return fig


def filtra_periodo(df, col, periodo):
    if df.empty or len(periodo) != 2:
        return df

    start = pd.to_datetime(periodo[0])
    end = pd.to_datetime(periodo[1])

    return df[(df[col] >= start) & (df[col] <= end)]


def calcola_cruscotto(prod, fermi):
    if prod.empty:
        return {
            "oee": 0,
            "disp_operativa": 0,
            "disp_tecnica": 0,
            "performance": 0,
            "quality": 0,
            "kg_molle": 0,
            "kg_teorici": 0,
            "kg_reali": 0,
            "kg_nc": 0,
            "resa": 0,
        }

    n_turni = prod[["data", "turno"]].drop_duplicates().shape[0]
    tempo_pianificato = n_turni * TURNO_H

    fermi_tot = fermi["durata_h"].sum() if not fermi.empty else 0
    fermi_tec = fermi[fermi["causale_fermo"].isin(CAUSALI_TECNICHE)]["durata_h"].sum() if not fermi.empty else 0

    disp_operativa = max(0, safe_div(tempo_pianificato - fermi_tot, tempo_pianificato))
    disp_tecnica = max(0, safe_div(tempo_pianificato - fermi_tec, tempo_pianificato))

    anag = leggi_prodotti()[["codice_prodotto", "capacita_kg_h"]]
    p = prod.merge(anag, on="codice_prodotto", how="left")
    p["capacita_kg_h"] = pd.to_numeric(p["capacita_kg_h"], errors="coerce").fillna(20)
    p["kg_teorici_macchina"] = p["capacita_kg_h"] * p["ore_produzione"]

    kg_reali = p["kg_polvere_reale"].sum()
    performance = safe_div(kg_reali, p["kg_teorici_macchina"].sum())

    analizzati = prod[prod["stato_analisi"].isin(["CONFORME", "NON_CONFORME"])].copy()

    if analizzati.empty:
        quality = 0
    else:
        quality = safe_div(analizzati["kg_conformi"].sum(), analizzati["kg_polvere_reale"].sum())

    oee = disp_operativa * performance * quality

    return {
        "oee": oee,
        "disp_operativa": disp_operativa,
        "disp_tecnica": disp_tecnica,
        "performance": performance,
        "quality": quality,
        "kg_molle": prod["kg_molle"].sum(),
        "kg_teorici": prod["kg_polvere_teorica"].sum(),
        "kg_reali": kg_reali,
        "kg_nc": prod["kg_nc"].sum(),
        "resa": safe_div(kg_reali, prod["kg_polvere_teorica"].sum()),
    }


# =========================
# SESSION STATE
# =========================

inizializza_file()

if "eventi_turno" not in st.session_state:
    st.session_state["eventi_turno"] = []

if "evento_da_modificare" not in st.session_state:
    st.session_state["evento_da_modificare"] = None

if "salvato" not in st.session_state:
    st.session_state["salvato"] = False


# =========================
# APP
# =========================

st.title("Dashboard OEE Spray Dryer - V12")

if st.session_state["salvato"]:
    st.session_state["salvato"] = False
    st.success("Operazione salvata correttamente.")

tab_turno, tab_qualita, tab_cruscotto, tab_formule, tab_prodotti, tab_gestione = st.tabs([
    "Turno",
    "Qualità",
    "Cruscotto OEE",
    "Assunzioni e formule",
    "Anagrafica prodotti",
    "Gestione dati",
])


# =========================
# TURNO
# =========================

with tab_turno:
    st.subheader("Compilazione turno")

    c0, c1 = st.columns(2)
    with c0:
        data_turno = st.date_input("Data turno")
    with c1:
        turno = st.selectbox("Turno", ["1", "2", "3"])

    st.caption(
        f"Turno {turno}: {TURNI[turno]['inizio'].strftime('%H:%M')} - "
        f"{TURNI[turno]['fine'].strftime('%H:%M')} | Durata pianificata: 8 h"
    )

    st.divider()
    st.markdown("### Aggiungi evento")

    prodotti = leggi_prodotti()
    prodotti["label"] = prodotti["codice_prodotto"].astype(str) + " - " + prodotti["descrizione_prodotto"].astype(str)

    idx_mod = st.session_state["evento_da_modificare"]

    evento_mod = None
    if idx_mod is not None and 0 <= idx_mod < len(st.session_state["eventi_turno"]):
        evento_mod = st.session_state["eventi_turno"][idx_mod]
        st.info(f"Modifica attiva: evento {idx_mod + 1} - {evento_mod['tipo_evento']}")

    default_tipo = evento_mod["tipo_evento"] if evento_mod else "Produzione"
    default_tipo_index = TIPI_EVENTO.index(default_tipo) if default_tipo in TIPI_EVENTO else 0

    with st.form("form_evento", clear_on_submit=False):
        tipo_evento = st.selectbox("Tipo evento", TIPI_EVENTO, index=default_tipo_index)

        default_start = parse_time_str(
            evento_mod["ora_inizio"] if evento_mod else "",
            TURNI[turno]["inizio"]
        )
        default_end = parse_time_str(
            evento_mod["ora_fine"] if evento_mod else "",
            TURNI[turno]["fine"]
        )

        c2, c3 = st.columns(2)
        with c2:
            ora_inizio = st.time_input("Ora inizio evento", value=default_start)
        with c3:
            ora_fine = st.time_input("Ora fine evento", value=default_end)

        durata_h = ore_da_orari(ora_inizio, ora_fine)

        if durata_h <= 0:
            st.warning("Inserire ora inizio e ora fine evento valide.")
        else:
            st.metric("Durata evento", f"{durata_h:.2f} h")

        evento = {
            "tipo_evento": tipo_evento,
            "ora_inizio": str(ora_inizio),
            "ora_fine": str(ora_fine),
            "durata_h": durata_h,
            "codice_prodotto": "",
            "descrizione_prodotto": "",
            "lotto": "",
            "kg_molle": 0.0,
            "residuo_secco": 0.0,
            "kg_polvere_teorica": 0.0,
            "kg_polvere_reale": 0.0,
            "note": "",
        }

        if tipo_evento == "Produzione":
            default_codice = evento_mod["codice_prodotto"] if evento_mod else ""
            labels = prodotti["label"].tolist()
            default_prod_idx = 0

            if default_codice:
                matches = prodotti.index[prodotti["codice_prodotto"].astype(str) == str(default_codice)].tolist()
                if matches:
                    default_prod_idx = prodotti.index.get_loc(matches[0])

            prodotto_label = st.selectbox("Prodotto", labels, index=default_prod_idx)
            prodotto = prodotti[prodotti["label"] == prodotto_label].iloc[0]

            lotto = st.text_input("Lotto", value=evento_mod["lotto"] if evento_mod else "")

            p1, p2 = st.columns(2)
            with p1:
                kg_molle = st.number_input(
                    "Kg estratto molle inserito",
                    min_value=0.0,
                    step=1.0,
                    value=float(evento_mod["kg_molle"]) if evento_mod else 0.0
                )
            with p2:
                residuo_secco = st.number_input(
                    "Residuo secco %",
                    min_value=0.0,
                    max_value=100.0,
                    step=0.1,
                    value=float(evento_mod["residuo_secco"]) if evento_mod else 0.0
                )

            kg_polvere_teorica = kg_molle * residuo_secco / 100
            st.metric("Kg polvere teorica", f"{kg_polvere_teorica:.2f} kg")

            kg_polvere_reale = st.number_input(
                "Kg polvere prodotta",
                min_value=0.0,
                step=1.0,
                value=float(evento_mod["kg_polvere_reale"]) if evento_mod else 0.0
            )

            evento.update({
                "codice_prodotto": prodotto["codice_prodotto"],
                "descrizione_prodotto": prodotto["descrizione_prodotto"],
                "lotto": lotto,
                "kg_molle": kg_molle,
                "residuo_secco": residuo_secco,
                "kg_polvere_teorica": kg_polvere_teorica,
                "kg_polvere_reale": kg_polvere_reale,
            })

        else:
            note = st.text_area("Note evento", value=evento_mod["note"] if evento_mod else "")
            evento["note"] = note

        if evento_mod is None:
            submit_evento = st.form_submit_button("Aggiungi evento al turno", type="primary")
            submit_modifica = False
            submit_annulla = False
        else:
            b1, b2 = st.columns(2)
            with b1:
                submit_modifica = st.form_submit_button("Salva modifiche evento", type="primary")
            with b2:
                submit_annulla = st.form_submit_button("Annulla modifica", type="secondary")
            submit_evento = False

    if submit_evento or submit_modifica:
        if durata_h <= 0:
            st.error("Controlla la durata evento.")
        elif tipo_evento == "Produzione" and evento["lotto"].strip() == "":
            st.error("Per una produzione devi inserire il lotto.")
        elif tipo_evento == "Produzione" and durata_h < (1 / 60):
            st.error("La produzione deve durare almeno 1 minuto.")
        else:
            if submit_modifica and idx_mod is not None:
                st.session_state["eventi_turno"][idx_mod] = evento
                st.session_state["evento_da_modificare"] = None
            else:
                st.session_state["eventi_turno"].append(evento)

            st.rerun()

    if submit_annulla:
        st.session_state["evento_da_modificare"] = None
        st.rerun()

    st.divider()
    st.markdown("### Eventi inseriti nel turno")

    eventi_df = pd.DataFrame(st.session_state["eventi_turno"])

    if eventi_df.empty:
        st.info("Nessun evento inserito.")
    else:
        st.dataframe(eventi_df, use_container_width=True)

        st.markdown("### Gestione evento selezionato")

        indice_evento = st.selectbox(
            "Seleziona evento",
            range(len(eventi_df)),
            format_func=lambda x: (
                f"{x + 1} - {eventi_df.iloc[x]['tipo_evento']} "
                f"({eventi_df.iloc[x]['ora_inizio']} - {eventi_df.iloc[x]['ora_fine']})"
            )
        )

        ge1, ge2, ge3 = st.columns(3)

        with ge1:
            if st.button("Modifica evento", type="primary"):
                st.session_state["evento_da_modificare"] = indice_evento
                st.rerun()

        with ge2:
            if st.button("Elimina evento", type="secondary"):
                st.session_state["eventi_turno"].pop(indice_evento)
                st.session_state["evento_da_modificare"] = None
                st.rerun()

        with ge3:
            if st.button("Duplica evento", type="secondary"):
                nuovo = st.session_state["eventi_turno"][indice_evento].copy()
                st.session_state["eventi_turno"].insert(indice_evento + 1, nuovo)
                st.rerun()

        ore_produzione = eventi_df[eventi_df["tipo_evento"] == "Produzione"]["durata_h"].sum()
        ore_fermo = eventi_df[eventi_df["tipo_evento"] != "Produzione"]["durata_h"].sum()
        kg_molle_tot = eventi_df["kg_molle"].sum()
        kg_teorici_tot = eventi_df["kg_polvere_teorica"].sum()
        kg_reali_tot = eventi_df["kg_polvere_reale"].sum()

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Ore produzione", f"{ore_produzione:.2f}")
        r2.metric("Ore fermo", f"{ore_fermo:.2f}")
        r3.metric("Kg molle", f"{kg_molle_tot:.1f}")
        r4.metric("Kg polvere", f"{kg_reali_tot:.1f}")

        r5, r6, r7 = st.columns(3)
        r5.metric("Kg teorici", f"{kg_teorici_tot:.1f}")
        r6.metric("Resa turno", f"{safe_div(kg_reali_tot, kg_teorici_tot):.1%}")
        r7.metric("Copertura turno", f"{safe_div(ore_produzione + ore_fermo, TURNO_H):.1%}")

        copertura_ore = ore_produzione + ore_fermo
        scostamento = copertura_ore - TURNO_H

        if abs(scostamento) <= 0.01:
            st.markdown(
                "<div class='alert-ok'>Copertura turno corretta: gli eventi coprono le 8 ore pianificate.</div>",
                unsafe_allow_html=True
            )
        elif scostamento > 0:
            st.markdown(
                f"<div class='alert-standby'>Attenzione: gli eventi superano il turno di {scostamento:.2f} h. Il turno resta in stand-by.</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='alert-standby'>Attenzione: mancano {abs(scostamento):.2f} h per coprire le 8 ore. Il turno resta in stand-by.</div>",
                unsafe_allow_html=True
            )

        c_reset, c_save = st.columns(2)

        with c_reset:
            if st.button("Svuota eventi turno", type="secondary"):
                reset_eventi_turno()
                st.rerun()

        with c_save:
            if st.button("Salva turno", type="primary"):
                if abs(copertura_ore - TURNO_H) > 0.01:
                    st.error(
                        "Turno non salvato: la somma degli eventi non coincide con le 8 ore pianificate. "
                        "Correggi o aggiungi gli eventi mancanti."
                    )
                    st.stop()

                if ore_produzione < (1 / 60):
                    st.error("Turno non salvato: serve almeno una produzione di durata pari o superiore a 1 minuto.")
                    st.stop()

                id_turno = nuovo_id()

                prod_rows = []
                fermi_rows = []

                for i, ev in enumerate(st.session_state["eventi_turno"], start=1):
                    if ev["tipo_evento"] == "Produzione":
                        prod_rows.append({
                            "id_lotto": f"{id_turno}-P{i}",
                            "id_turno": id_turno,
                            "data": str(data_turno),
                            "turno": turno,
                            "codice_prodotto": ev["codice_prodotto"],
                            "descrizione_prodotto": ev["descrizione_prodotto"],
                            "lotto": ev["lotto"],
                            "kg_molle": ev["kg_molle"],
                            "residuo_secco": ev["residuo_secco"],
                            "kg_polvere_teorica": ev["kg_polvere_teorica"],
                            "kg_polvere_reale": ev["kg_polvere_reale"],
                            "ora_inizio": ev["ora_inizio"],
                            "ora_fine": ev["ora_fine"],
                            "ore_produzione": ev["durata_h"],
                            "stato_analisi": "ATTESA_ANALISI",
                            "kg_conformi": 0,
                            "kg_nc": 0,
                            "causa_nc": "",
                            "note_nc": "",
                            "data_rilascio_analisi": "",
                        })
                    else:
                        fermi_rows.append({
                            "id_fermo": f"{id_turno}-F{i}",
                            "id_turno": id_turno,
                            "data": str(data_turno),
                            "turno": turno,
                            "ora_inizio": ev["ora_inizio"],
                            "ora_fine": ev["ora_fine"],
                            "durata_h": ev["durata_h"],
                            "causale_fermo": ev["tipo_evento"],
                            "note_fermo": ev["note"],
                        })

                prod = leggi_produzioni()
                fermi = leggi_fermi()

                if prod_rows:
                    prod = pd.concat([prod, pd.DataFrame(prod_rows)], ignore_index=True)
                    salva_csv(prod, PRODUZIONI_FILE, COL_PRODUZIONI)

                if fermi_rows:
                    fermi = pd.concat([fermi, pd.DataFrame(fermi_rows)], ignore_index=True)
                    salva_csv(fermi, FERMI_FILE, COL_FERMI)

                reset_eventi_turno()
                st.session_state["salvato"] = True
                st.rerun()


# =========================
# QUALITÀ
# =========================

with tab_qualita:
    st.subheader("Lotti in attesa analisi")

    prod = prepara_produzioni(leggi_produzioni())

    if prod.empty:
        st.info("Nessuna produzione registrata.")
    else:
        attesa = prod[prod["stato_analisi"] == "ATTESA_ANALISI"].copy()

        if attesa.empty:
            st.info("Nessun lotto in attesa analisi.")
        else:
            attesa["label"] = (
                attesa["lotto"].astype(str) + " | " +
                attesa["codice_prodotto"].astype(str) + " | " +
                attesa["data"].dt.strftime("%d/%m/%Y")
            )

            label = st.selectbox("Seleziona lotto", attesa["label"].tolist())
            lotto_sel = attesa[attesa["label"] == label].iloc[0]

            st.write("Prodotto:", lotto_sel["descrizione_prodotto"])
            st.write("Kg prodotti:", lotto_sel["kg_polvere_reale"])

            with st.form("form_qualita"):
                esito = st.radio("Esito", ["CONFORME", "NON_CONFORME"], horizontal=True)

                if esito == "CONFORME":
                    kg_conformi = float(lotto_sel["kg_polvere_reale"])
                    kg_nc = 0.0
                    causa_nc = ""
                    note_nc = ""
                    st.metric("Kg conformi", f"{kg_conformi:.2f}")
                else:
                    kg_conformi = st.number_input(
                        "Kg conformi",
                        min_value=0.0,
                        max_value=float(lotto_sel["kg_polvere_reale"]),
                        step=1.0
                    )
                    kg_nc = max(float(lotto_sel["kg_polvere_reale"]) - kg_conformi, 0)
                    st.metric("Kg NC", f"{kg_nc:.2f}")
                    causa_nc = st.selectbox("Causa NC", CAUSE_NC)
                    note_nc = st.text_area("Note NC")

                data_rilascio = st.date_input("Data rilascio analisi")
                salva_esito = st.form_submit_button("Salva esito analisi", type="primary")

            if salva_esito:
                df = leggi_produzioni()
                mask = df["id_lotto"].astype(str) == str(lotto_sel["id_lotto"])

                if not mask.any():
                    st.error("Lotto non trovato nello storico produzioni.")
                else:
                    df = assegna_valore(df, mask, "stato_analisi", esito)
                    df = assegna_valore(df, mask, "kg_conformi", kg_conformi)
                    df = assegna_valore(df, mask, "kg_nc", kg_nc)
                    df = assegna_valore(df, mask, "causa_nc", causa_nc)
                    df = assegna_valore(df, mask, "note_nc", note_nc)
                    df = assegna_valore(df, mask, "data_rilascio_analisi", data_rilascio)

                    salva_csv(df, PRODUZIONI_FILE, COL_PRODUZIONI)
                    st.session_state["salvato"] = True
                    st.rerun()


# =========================
# CRUSCOTTO
# =========================

with tab_cruscotto:
    st.subheader("Cruscotto OEE")

    prod = prepara_produzioni(leggi_produzioni())
    fermi = prepara_fermi(leggi_fermi())

    if prod.empty:
        st.info("Nessuna produzione registrata.")
    else:
        min_data = prod["data"].min().date()
        max_data = prod["data"].max().date()

        c1, c2, c3 = st.columns(3)
        with c1:
            periodo = st.date_input("Periodo", value=[min_data, max_data])
        with c2:
            filtro_prodotto = st.selectbox("Filtro prodotto", ["Tutti"] + sorted(prod["codice_prodotto"].dropna().unique().tolist()))
        with c3:
            filtro_turno = st.selectbox("Filtro turno", ["Tutti"] + sorted(prod["turno"].dropna().astype(str).unique().tolist()))

        prod_f = filtra_periodo(prod, "data", periodo)
        fermi_f = filtra_periodo(fermi, "data", periodo) if not fermi.empty else fermi

        if filtro_prodotto != "Tutti":
            prod_f = prod_f[prod_f["codice_prodotto"] == filtro_prodotto]

        if filtro_turno != "Tutti":
            prod_f = prod_f[prod_f["turno"].astype(str) == filtro_turno]
            if not fermi_f.empty:
                fermi_f = fermi_f[fermi_f["turno"].astype(str) == filtro_turno]

        kpi = calcola_cruscotto(prod_f, fermi_f)

        a, b = st.columns([1.2, 1])
        with a:
            st.plotly_chart(gauge_oee(kpi["oee"]), use_container_width=True)
        with b:
            st.metric("Disponibilità operativa", f"{kpi['disp_operativa']:.1%}")
            st.metric("Disponibilità tecnica", f"{kpi['disp_tecnica']:.1%}")
            st.metric("Performance", f"{kpi['performance']:.1%}")
            st.metric("Qualità", f"{kpi['quality']:.1%}")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Kg molle", f"{kpi['kg_molle']:.1f}")
        m2.metric("Kg teorici", f"{kpi['kg_teorici']:.1f}")
        m3.metric("Kg reali", f"{kpi['kg_reali']:.1f}")
        m4.metric("Resa", f"{kpi['resa']:.1%}")

        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Lotti prodotti", len(prod_f))
        q2.metric("Attesa analisi", len(prod_f[prod_f["stato_analisi"] == "ATTESA_ANALISI"]))
        q3.metric("Conformi", len(prod_f[prod_f["stato_analisi"] == "CONFORME"]))
        q4.metric("NC", len(prod_f[prod_f["stato_analisi"] == "NON_CONFORME"]))

        st.divider()

        g1, g2 = st.columns(2)
        with g1:
            if fermi_f.empty:
                st.info("Nessun fermo.")
            else:
                fermo_causa = fermi_f.groupby("causale_fermo", as_index=False)["durata_h"].sum()
                st.plotly_chart(
                    px.bar(fermo_causa, x="causale_fermo", y="durata_h", title="Ore fermo per causale"),
                    use_container_width=True
                )

        with g2:
            nc = prod_f[prod_f["stato_analisi"] == "NON_CONFORME"]
            if nc.empty:
                st.info("Nessuna NC.")
            else:
                nc_causa = nc.groupby("causa_nc", as_index=False)["kg_nc"].sum()
                st.plotly_chart(
                    px.bar(nc_causa, x="causa_nc", y="kg_nc", title="Kg NC per causa"),
                    use_container_width=True
                )

        st.subheader("Produzioni filtrate")
        st.dataframe(prod_f, use_container_width=True)


# =========================
# FORMULE
# =========================

with tab_formule:
    st.subheader("Assunzioni e formule")

    st.markdown("""
### Logica operativa

L'operatore compila un unico turno tramite eventi.  
Gli eventi di tipo **Produzione** generano automaticamente lotti in **ATTESA_ANALISI**.

### Tempo pianificato

Ogni turno vale **8 ore**.

### Polvere teorica

`kg polvere teorica = kg molle × residuo secco % / 100`

### Resa

`resa = kg polvere reale / kg polvere teorica`

### Disponibilità operativa

`disponibilità operativa = (tempo pianificato - tutti i fermi) / tempo pianificato`

### Disponibilità tecnica

Considera solo:

- Guasto
- Manutenzione straordinaria

`disponibilità tecnica = (tempo pianificato - fermi tecnici) / tempo pianificato`

### Performance

`performance = kg polvere reale / (capacità nominale prodotto × ore produzione)`

La capacità nominale è gestita in **Anagrafica prodotti**. Default: **20 kg/h**.

### Qualità

La qualità considera solo i lotti rilasciati dal laboratorio.

`qualità = kg conformi / kg prodotti analizzati`

### OEE

`OEE = disponibilità operativa × performance × qualità`
""")


# =========================
# ANAGRAFICA PRODOTTI
# =========================

with tab_prodotti:
    st.subheader("Anagrafica prodotti")

    prodotti = leggi_prodotti()
    st.dataframe(prodotti, use_container_width=True)

    with st.form("form_prodotto"):
        codice = st.text_input("Codice prodotto")
        descrizione = st.text_input("Descrizione prodotto")
        capacita = st.number_input("Capacità nominale kg/h", min_value=0.0, value=20.0, step=1.0)
        salva_prod = st.form_submit_button("Salva prodotto", type="primary")

    if salva_prod:
        if codice.strip() == "" or descrizione.strip() == "":
            st.error("Inserisci codice e descrizione.")
        else:
            nuovo = pd.DataFrame([{
                "codice_prodotto": codice.strip(),
                "descrizione_prodotto": descrizione.strip(),
                "capacita_kg_h": capacita,
            }])

            prodotti = pd.concat([prodotti, nuovo], ignore_index=True)
            prodotti = prodotti.drop_duplicates(subset=["codice_prodotto"], keep="last")
            salva_csv(prodotti, PRODOTTI_FILE, COL_PRODOTTI)

            st.session_state["salvato"] = True
            st.rerun()


# =========================
# GESTIONE DATI PROTETTA
# =========================

with tab_gestione:
    st.subheader("Gestione dati riservata")

    st.warning(
        "Questa sezione consente modifiche a posteriori su produzioni e fermi già salvati. "
        "Usarla solo per correzioni autorizzate."
    )

    password = st.text_input("Password gestione", type="password")

    if password != ADMIN_PASSWORD:
        st.info("Inserisci la password per abilitare modifica/eliminazione degli eventi salvati.")
        st.stop()

    st.success("Accesso gestione abilitato.")

    st.markdown("## Produzioni salvate")

    prod = leggi_produzioni()
    st.dataframe(prod, use_container_width=True)

    if not prod.empty:
        id_lotto = st.selectbox("Seleziona produzione", prod["id_lotto"].astype(str).tolist())
        prod_sel = prod[prod["id_lotto"].astype(str) == str(id_lotto)].iloc[0]

        with st.form("form_modifica_produzione"):
            c1, c2, c3 = st.columns(3)
            with c1:
                nuova_data = st.date_input(
                    "Data",
                    value=pd.to_datetime(prod_sel["data"], errors="coerce").date()
                    if not pd.isna(pd.to_datetime(prod_sel["data"], errors="coerce"))
                    else pd.Timestamp.today().date()
                )
            with c2:
                nuovo_turno = st.selectbox(
                    "Turno",
                    ["1", "2", "3"],
                    index=["1", "2", "3"].index(str(prod_sel["turno"])) if str(prod_sel["turno"]) in ["1", "2", "3"] else 0
                )
            with c3:
                nuovo_lotto = st.text_input("Lotto", value=str(prod_sel["lotto"]))

            nuovo_codice = st.text_input("Codice prodotto", value=str(prod_sel["codice_prodotto"]))
            nuova_descrizione = st.text_input("Descrizione prodotto", value=str(prod_sel["descrizione_prodotto"]))

            c4, c5, c6 = st.columns(3)
            with c4:
                nuovo_kg_molle = st.number_input("Kg molle", min_value=0.0, value=safe_float(prod_sel["kg_molle"]), step=1.0)
            with c5:
                nuovo_rs = st.number_input("Residuo secco %", min_value=0.0, max_value=100.0, value=safe_float(prod_sel["residuo_secco"]), step=0.1)
            with c6:
                nuovo_kg_reale = st.number_input("Kg polvere reale", min_value=0.0, value=safe_float(prod_sel["kg_polvere_reale"]), step=1.0)

            nuovo_kg_teorico = nuovo_kg_molle * nuovo_rs / 100
            st.metric("Kg polvere teorica ricalcolata", f"{nuovo_kg_teorico:.2f} kg")

            c7, c8, c9 = st.columns(3)
            with c7:
                nuova_ora_inizio = st.text_input("Ora inizio", value=str(prod_sel["ora_inizio"]))
            with c8:
                nuova_ora_fine = st.text_input("Ora fine", value=str(prod_sel["ora_fine"]))
            with c9:
                nuove_ore = st.number_input("Ore produzione", min_value=0.0, value=safe_float(prod_sel["ore_produzione"]), step=0.25)

            stato_base = str(prod_sel["stato_analisi"])
            if stato_base not in ["ATTESA_ANALISI", "CONFORME", "NON_CONFORME"]:
                stato_base = "ATTESA_ANALISI"

            nuovo_stato = st.selectbox(
                "Stato analisi",
                ["ATTESA_ANALISI", "CONFORME", "NON_CONFORME"],
                index=["ATTESA_ANALISI", "CONFORME", "NON_CONFORME"].index(stato_base)
            )

            c10, c11 = st.columns(2)
            with c10:
                nuovo_kg_conf = st.number_input("Kg conformi", min_value=0.0, value=safe_float(prod_sel["kg_conformi"]), step=1.0)
            with c11:
                nuovo_kg_nc = st.number_input("Kg NC", min_value=0.0, value=safe_float(prod_sel["kg_nc"]), step=1.0)

            nuova_causa = st.text_input("Causa NC", value="" if pd.isna(prod_sel["causa_nc"]) else str(prod_sel["causa_nc"]))
            nuove_note = st.text_area("Note NC", value="" if pd.isna(prod_sel["note_nc"]) else str(prod_sel["note_nc"]))

            salva_mod_prod = st.form_submit_button("Salva modifiche produzione", type="primary")

        if salva_mod_prod:
            mask = prod["id_lotto"].astype(str) == str(id_lotto)

            prod = assegna_valore(prod, mask, "data", nuova_data)
            prod = assegna_valore(prod, mask, "turno", nuovo_turno)
            prod = assegna_valore(prod, mask, "lotto", nuovo_lotto)
            prod = assegna_valore(prod, mask, "codice_prodotto", nuovo_codice)
            prod = assegna_valore(prod, mask, "descrizione_prodotto", nuova_descrizione)
            prod = assegna_valore(prod, mask, "kg_molle", nuovo_kg_molle)
            prod = assegna_valore(prod, mask, "residuo_secco", nuovo_rs)
            prod = assegna_valore(prod, mask, "kg_polvere_teorica", nuovo_kg_teorico)
            prod = assegna_valore(prod, mask, "kg_polvere_reale", nuovo_kg_reale)
            prod = assegna_valore(prod, mask, "ora_inizio", nuova_ora_inizio)
            prod = assegna_valore(prod, mask, "ora_fine", nuova_ora_fine)
            prod = assegna_valore(prod, mask, "ore_produzione", nuove_ore)
            prod = assegna_valore(prod, mask, "stato_analisi", nuovo_stato)
            prod = assegna_valore(prod, mask, "kg_conformi", nuovo_kg_conf)
            prod = assegna_valore(prod, mask, "kg_nc", nuovo_kg_nc)
            prod = assegna_valore(prod, mask, "causa_nc", nuova_causa)
            prod = assegna_valore(prod, mask, "note_nc", nuove_note)

            salva_csv(prod, PRODUZIONI_FILE, COL_PRODUZIONI)
            st.session_state["salvato"] = True
            st.rerun()

        if st.button("Elimina produzione selezionata", type="secondary"):
            prod = prod[prod["id_lotto"].astype(str) != str(id_lotto)]
            salva_csv(prod, PRODUZIONI_FILE, COL_PRODUZIONI)
            st.session_state["salvato"] = True
            st.rerun()

    st.divider()

    st.markdown("## Fermi salvati")

    fermi = leggi_fermi()
    st.dataframe(fermi, use_container_width=True)

    if not fermi.empty:
        id_fermo = st.selectbox("Seleziona fermo", fermi["id_fermo"].astype(str).tolist())
        fermo_sel = fermi[fermi["id_fermo"].astype(str) == str(id_fermo)].iloc[0]

        with st.form("form_modifica_fermo"):
            c1, c2, c3 = st.columns(3)
            with c1:
                nuova_data_f = st.date_input(
                    "Data fermo",
                    value=pd.to_datetime(fermo_sel["data"], errors="coerce").date()
                    if not pd.isna(pd.to_datetime(fermo_sel["data"], errors="coerce"))
                    else pd.Timestamp.today().date()
                )
            with c2:
                nuovo_turno_f = st.selectbox(
                    "Turno fermo",
                    ["1", "2", "3"],
                    index=["1", "2", "3"].index(str(fermo_sel["turno"])) if str(fermo_sel["turno"]) in ["1", "2", "3"] else 0
                )
            with c3:
                causale_corrente = str(fermo_sel["causale_fermo"])
                nuova_causale = st.selectbox(
                    "Causale fermo",
                    TIPI_EVENTO[1:],
                    index=TIPI_EVENTO[1:].index(causale_corrente) if causale_corrente in TIPI_EVENTO[1:] else 0
                )

            c4, c5, c6 = st.columns(3)
            with c4:
                nuova_ora_i_f = st.text_input("Ora inizio fermo", value=str(fermo_sel["ora_inizio"]))
            with c5:
                nuova_ora_f_f = st.text_input("Ora fine fermo", value=str(fermo_sel["ora_fine"]))
            with c6:
                nuova_durata = st.number_input("Durata fermo h", min_value=0.0, value=safe_float(fermo_sel["durata_h"]), step=0.25)

            nuove_note_f = st.text_area("Note fermo", value="" if pd.isna(fermo_sel["note_fermo"]) else str(fermo_sel["note_fermo"]))

            salva_mod_fermo = st.form_submit_button("Salva modifiche fermo", type="primary")

        if salva_mod_fermo:
            mask = fermi["id_fermo"].astype(str) == str(id_fermo)

            fermi = assegna_valore(fermi, mask, "data", nuova_data_f)
            fermi = assegna_valore(fermi, mask, "turno", nuovo_turno_f)
            fermi = assegna_valore(fermi, mask, "causale_fermo", nuova_causale)
            fermi = assegna_valore(fermi, mask, "ora_inizio", nuova_ora_i_f)
            fermi = assegna_valore(fermi, mask, "ora_fine", nuova_ora_f_f)
            fermi = assegna_valore(fermi, mask, "durata_h", nuova_durata)
            fermi = assegna_valore(fermi, mask, "note_fermo", nuove_note_f)

            salva_csv(fermi, FERMI_FILE, COL_FERMI)
            st.session_state["salvato"] = True
            st.rerun()

        if st.button("Elimina fermo selezionato", type="secondary"):
            fermi = fermi[fermi["id_fermo"].astype(str) != str(id_fermo)]
            salva_csv(fermi, FERMI_FILE, COL_FERMI)
            st.session_state["salvato"] = True
            st.rerun()

    st.divider()

    if st.button("Cancella tutto lo storico produzioni", type="secondary"):
        pd.DataFrame(columns=COL_PRODUZIONI).to_csv(PRODUZIONI_FILE, index=False)
        st.session_state["salvato"] = True
        st.rerun()

    if st.button("Cancella tutto lo storico fermi", type="secondary"):
        pd.DataFrame(columns=COL_FERMI).to_csv(FERMI_FILE, index=False)
        st.session_state["salvato"] = True
        st.rerun()
