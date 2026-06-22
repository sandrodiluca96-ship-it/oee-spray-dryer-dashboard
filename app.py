
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime
import math

st.set_page_config(page_title="OEE Spray Dryer", layout="wide")

DATABASE = Path("data/database.csv")
PRODOTTI_FILE = Path("data/prodotti.csv")
CAPACITA_MACCHINA_KG_H = 20

CAUSALI_FERMO = [
    "Nessun fermo",
    "Attesa prodotto",
    "Attesa analisi",
    "Manutenzione programmata",
    "Manutenzione straordinaria",
    "Lavaggio",
    "Cambio lotto",
    "Guasto",
    "Altro"
]

COLONNE_DATABASE = [
    "id_riga", "data", "turno", "codice_prodotto", "descrizione_prodotto", "lotto",
    "kg_molle", "residuo_secco", "kg_polvere_reale", "kg_polvere_conforme",
    "tempo_operativo_h", "fermi_h", "causale_fermo", "note_fermo", "motivazione_nc"
]

def inizializza_file():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    if not DATABASE.exists():
        pd.DataFrame(columns=COLONNE_DATABASE).to_csv(DATABASE, index=False)
    if not PRODOTTI_FILE.exists():
        pd.DataFrame(columns=["codice_prodotto", "descrizione_prodotto"]).to_csv(PRODOTTI_FILE, index=False)

def leggi_database():
    inizializza_file()
    df = pd.read_csv(DATABASE)
    for col in COLONNE_DATABASE:
        if col not in df.columns:
            if col == "causale_fermo":
                df[col] = "Nessun fermo"
            else:
                df[col] = None
    if not df.empty and df["id_riga"].isna().any():
        df["id_riga"] = [f"OLD-{i+1}" if pd.isna(v) else v for i, v in enumerate(df["id_riga"])]
        df[COLONNE_DATABASE].to_csv(DATABASE, index=False)
    return df[COLONNE_DATABASE]

def leggi_prodotti():
    inizializza_file()
    df = pd.read_csv(PRODOTTI_FILE)
    if df.empty:
        return pd.DataFrame([{"codice_prodotto": "INSERIRE", "descrizione_prodotto": "Inserire anagrafica prodotti"}])
    return df

def safe_div(num, den):
    if den is None or den == 0 or pd.isna(den):
        return 0
    return num / den

def calcola_kpi(df):
    if df.empty:
        return df
    numeric_cols = ["kg_molle", "residuo_secco", "kg_polvere_reale", "kg_polvere_conforme", "tempo_operativo_h", "fermi_h"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["kg_polvere_teorica"] = df["kg_molle"] * df["residuo_secco"] / 100
    df["kg_polvere_nc"] = (df["kg_polvere_reale"] - df["kg_polvere_conforme"]).clip(lower=0)
    df["resa"] = df.apply(lambda r: safe_div(r["kg_polvere_reale"], r["kg_polvere_teorica"]), axis=1)
    df["performance"] = df.apply(lambda r: safe_div(r["kg_polvere_reale"], CAPACITA_MACCHINA_KG_H * r["tempo_operativo_h"]), axis=1)
    df["quality"] = df.apply(lambda r: safe_div(r["kg_polvere_conforme"], r["kg_polvere_reale"]), axis=1)
    df["availability"] = df.apply(lambda r: safe_div(r["tempo_operativo_h"], r["tempo_operativo_h"] + r["fermi_h"]), axis=1)
    df["oee"] = df["availability"] * df["performance"] * df["quality"]
    for col in ["resa", "performance", "quality", "availability", "oee"]:
        df[col] = df[col].replace([math.inf, -math.inf], 0).fillna(0)
    return df

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
            "threshold": {"line": {"color": "black", "width": 4}, "thickness": 0.75, "value": 75}
        }
    ))
    fig.update_layout(height=330, margin=dict(l=30, r=30, t=70, b=20))
    return fig

inizializza_file()
st.title("Dashboard OEE Spray Dryer")

if "form_salvato" not in st.session_state:
    st.session_state["form_salvato"] = False

if st.session_state["form_salvato"]:
    st.session_state["form_salvato"] = False
    st.success("Dati salvati correttamente. Il modulo è stato svuotato.")

tab_inserimento, tab_cruscotto, tab_assunzioni, tab_prodotti, tab_gestione = st.tabs([
    "Inserimento dati", "Cruscotto OEE", "Assunzioni e formule", "Anagrafica prodotti", "Gestione dati"
])

with tab_inserimento:
    st.subheader("Inserimento dati produzione")
    prodotti = leggi_prodotti()
    prodotti["label"] = prodotti["codice_prodotto"].astype(str) + " - " + prodotti["descrizione_prodotto"].astype(str)

    with st.form("inserimento_dati", clear_on_submit=True):
        data = st.date_input("Data")
        turno = st.selectbox("Turno", ["1", "2", "3"])

        prodotto_label = st.selectbox(
            "Prodotto",
            prodotti["label"].tolist(),
            help="Scrivi nel campo per cercare codice o descrizione prodotto."
        )
        prodotto_selezionato = prodotti[prodotti["label"] == prodotto_label].iloc[0]
        codice_prodotto = prodotto_selezionato["codice_prodotto"]
        descrizione_prodotto = prodotto_selezionato["descrizione_prodotto"]
        st.info(f"Codice: {codice_prodotto} | Descrizione: {descrizione_prodotto}")

        lotto = st.text_input("Lotto")

        c1, c2 = st.columns(2)
        with c1:
            kg_molle = st.number_input("Kg estratto molle inserito", min_value=0.0, step=1.0)
        with c2:
            residuo_secco = st.number_input("Residuo secco %", min_value=0.0, max_value=100.0, step=0.1)

        kg_polvere_teorica = kg_molle * residuo_secco / 100
        st.metric("Polvere teorica calcolata", f"{kg_polvere_teorica:.2f} kg")

        c3, c4 = st.columns(2)
        with c3:
            kg_polvere_reale = st.number_input("Kg polvere reale prodotta", min_value=0.0, step=1.0)
        with c4:
            kg_polvere_conforme = st.number_input("Kg polvere conforme", min_value=0.0, step=1.0)

        kg_polvere_nc = max(kg_polvere_reale - kg_polvere_conforme, 0)
        st.metric("Kg polvere non conforme", f"{kg_polvere_nc:.2f} kg")

        c5, c6 = st.columns(2)
        with c5:
            tempo_operativo_h = st.number_input("Ore operative", min_value=0.0, step=0.5)
        with c6:
            fermi_h = st.number_input("Ore fermo", min_value=0.0, step=0.5)

        causale_fermo = st.selectbox("Causale fermo principale", CAUSALI_FERMO)
        note_fermo = st.text_area("Note fermo", placeholder="Dettaglio del fermo, se necessario")
        motivazione_nc = st.text_area("Motivazione NC", placeholder="Esempio: umidità alta, granulometria fuori specifica, colore non conforme...")

        salva = st.form_submit_button("Salva dati")

    if salva:
        if lotto.strip() == "":
            st.error("Inserisci il lotto prima di salvare.")
        else:
            df_db = leggi_database()
            duplicato = df_db[
                (df_db["data"].astype(str) == str(data)) &
                (df_db["turno"].astype(str) == str(turno)) &
                (df_db["codice_prodotto"].astype(str) == str(codice_prodotto)) &
                (df_db["lotto"].astype(str) == str(lotto))
            ]
            if not duplicato.empty:
                st.warning("Registrazione già presente con stessa data, turno, prodotto e lotto. Riga non salvata per evitare doppioni.")
            else:
                nuova_riga = pd.DataFrame([{
                    "id_riga": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "data": data,
                    "turno": turno,
                    "codice_prodotto": codice_prodotto,
                    "descrizione_prodotto": descrizione_prodotto,
                    "lotto": lotto,
                    "kg_molle": kg_molle,
                    "residuo_secco": residuo_secco,
                    "kg_polvere_reale": kg_polvere_reale,
                    "kg_polvere_conforme": kg_polvere_conforme,
                    "tempo_operativo_h": tempo_operativo_h,
                    "fermi_h": fermi_h,
                    "causale_fermo": causale_fermo,
                    "note_fermo": note_fermo,
                    "motivazione_nc": motivazione_nc
                }])
                df_db = pd.concat([df_db, nuova_riga], ignore_index=True)
                df_db.to_csv(DATABASE, index=False)
                st.session_state["form_salvato"] = True
                st.rerun()

with tab_cruscotto:
    df = calcola_kpi(leggi_database())
    if df.empty:
        st.info("Nessun dato ancora inserito.")
    else:
        st.subheader("Cruscotto automatico OEE")
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_prodotto = st.selectbox("Filtro prodotto", ["Tutti"] + sorted(df["codice_prodotto"].dropna().unique().tolist()))
        with col_f2:
            filtro_turno = st.selectbox("Filtro turno", ["Tutti"] + sorted(df["turno"].dropna().astype(str).unique().tolist()))
        with col_f3:
            periodo = st.date_input("Periodo", value=[
                df["data"].min().date() if not pd.isna(df["data"].min()) else pd.Timestamp.today().date(),
                df["data"].max().date() if not pd.isna(df["data"].max()) else pd.Timestamp.today().date()
            ])
        df_f = df.copy()
        if filtro_prodotto != "Tutti":
            df_f = df_f[df_f["codice_prodotto"] == filtro_prodotto]
        if filtro_turno != "Tutti":
            df_f = df_f[df_f["turno"].astype(str) == filtro_turno]
        if len(periodo) == 2:
            start, end = pd.to_datetime(periodo[0]), pd.to_datetime(periodo[1])
            df_f = df_f[(df_f["data"] >= start) & (df_f["data"] <= end)]
        if df_f.empty:
            st.warning("Nessun dato disponibile per i filtri selezionati.")
        else:
            c1, c2 = st.columns([1.2, 1])
            with c1:
                st.plotly_chart(gauge_oee(df_f["oee"].mean()), use_container_width=True)
            with c2:
                st.metric("Disponibilità", f"{df_f['availability'].mean():.1%}")
                st.metric("Performance", f"{df_f['performance'].mean():.1%}")
                st.metric("Qualità", f"{df_f['quality'].mean():.1%}")
                st.metric("Resa processo", f"{df_f['resa'].mean():.1%}")

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Kg molle", f"{df_f['kg_molle'].sum():.1f}")
            k2.metric("Kg polvere teorica", f"{df_f['kg_polvere_teorica'].sum():.1f}")
            k3.metric("Kg polvere reale", f"{df_f['kg_polvere_reale'].sum():.1f}")
            k4.metric("Kg NC", f"{df_f['kg_polvere_nc'].sum():.1f}")

            fig_trend = px.line(df_f.sort_values("data"), x="data", y=["oee", "availability", "performance", "quality", "resa"], markers=True, title="Trend KPI")
            fig_trend.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig_trend, use_container_width=True)

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                df_fermi = df_f[df_f["fermi_h"] > 0].groupby("causale_fermo", as_index=False)["fermi_h"].sum()
                if df_fermi.empty:
                    st.info("Nessun fermo registrato nel periodo.")
                else:
                    st.plotly_chart(px.bar(df_fermi, x="causale_fermo", y="fermi_h", title="Ore fermo per causale"), use_container_width=True)
            with col_g2:
                df_nc = df_f[df_f["kg_polvere_nc"] > 0].copy()
                if df_nc.empty:
                    st.info("Nessuna NC registrata nel periodo.")
                else:
                    df_nc["motivazione_nc"] = df_nc["motivazione_nc"].fillna("Non specificata")
                    st.plotly_chart(px.bar(df_nc.groupby("motivazione_nc", as_index=False)["kg_polvere_nc"].sum(), x="motivazione_nc", y="kg_polvere_nc", title="NC per motivazione"), use_container_width=True)

            st.subheader("Storico produzioni")
            st.dataframe(df_f, use_container_width=True)

with tab_assunzioni:
    st.subheader("Assunzioni e formule utilizzate")
    st.markdown("""
### Capacità nominale macchina
**20 kg polvere/h**.

### Polvere teorica
`kg polvere teorica = kg molle × residuo secco % / 100`

### Resa di processo
`resa = kg polvere reale / kg polvere teorica`

### Disponibilità
`disponibilità = ore operative / (ore operative + ore fermo)`

### Performance
`performance = kg polvere reale / (20 × ore operative)`

### Qualità
`qualità = kg polvere conforme / kg polvere reale`

### OEE
`OEE = disponibilità × performance × qualità`

### Fermi
La causale fermo viene scelta da un menu:
**Attesa prodotto, Attesa analisi, Manutenzione programmata, Manutenzione straordinaria, Lavaggio, Cambio lotto, Guasto, Altro**.
""")

with tab_prodotti:
    st.subheader("Anagrafica prodotti")
    prodotti = leggi_prodotti()
    st.dataframe(prodotti, use_container_width=True)
    with st.form("nuovo_prodotto"):
        st.markdown("### Aggiungi prodotto")
        nuovo_codice = st.text_input("Codice prodotto")
        nuova_descrizione = st.text_input("Descrizione prodotto")
        aggiungi = st.form_submit_button("Aggiungi prodotto")
    if aggiungi:
        if nuovo_codice.strip() == "" or nuova_descrizione.strip() == "":
            st.error("Inserisci sia codice sia descrizione.")
        else:
            nuova_riga = pd.DataFrame([{"codice_prodotto": nuovo_codice.strip(), "descrizione_prodotto": nuova_descrizione.strip()}])
            prodotti = pd.concat([prodotti, nuova_riga], ignore_index=True).drop_duplicates(subset=["codice_prodotto"], keep="last")
            prodotti.to_csv(PRODOTTI_FILE, index=False)
            st.success("Prodotto aggiunto correttamente. Aggiorna la pagina.")

with tab_gestione:
    st.subheader("Gestione dati registrati")
    df = leggi_database()
    if df.empty:
        st.info("Nessun dato da gestire.")
    else:
        st.dataframe(df, use_container_width=True)
        riga_da_eliminare = st.selectbox("Seleziona riga da eliminare", df["id_riga"].astype(str).tolist())
        if st.button("Elimina riga selezionata"):
            df = df[df["id_riga"].astype(str) != str(riga_da_eliminare)]
            df.to_csv(DATABASE, index=False)
            st.success("Riga eliminata. Aggiorna la pagina.")
        if st.button("Cancella tutto lo storico"):
            pd.DataFrame(columns=COLONNE_DATABASE).to_csv(DATABASE, index=False)
            st.success("Storico cancellato. Aggiorna la pagina.")
