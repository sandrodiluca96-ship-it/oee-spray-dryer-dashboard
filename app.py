import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import math

st.set_page_config(page_title="OEE Spray Dryer", layout="wide")

DATABASE = Path("data/database.csv")
PRODOTTI_FILE = Path("data/prodotti.csv")
CAPACITA_MACCHINA_KG_H = 20

COLONNE_DATABASE = [
    "data", "turno", "codice_prodotto", "descrizione_prodotto", "lotto",
    "kg_molle", "residuo_secco", "kg_polvere_reale", "kg_polvere_conforme",
    "tempo_operativo_h", "fermi_h", "motivazione_nc"
]

def inizializza_file():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)

    if not DATABASE.exists():
        pd.DataFrame(columns=COLONNE_DATABASE).to_csv(DATABASE, index=False)

    if not PRODOTTI_FILE.exists():
        prodotti_demo = pd.DataFrame([
            {"codice_prodotto": "W-SD-001", "descrizione_prodotto": "Estratto secco spray dryer - prodotto demo 1"},
            {"codice_prodotto": "W-SD-002", "descrizione_prodotto": "Estratto secco spray dryer - prodotto demo 2"},
            {"codice_prodotto": "W-SD-003", "descrizione_prodotto": "Semilavorato vegetale in polvere - prodotto demo 3"},
        ])
        prodotti_demo.to_csv(PRODOTTI_FILE, index=False)

def leggi_database():
    inizializza_file()
    df = pd.read_csv(DATABASE)
    for col in COLONNE_DATABASE:
        if col not in df.columns:
            df[col] = None
    return df[COLONNE_DATABASE]

def leggi_prodotti():
    inizializza_file()
    return pd.read_csv(PRODOTTI_FILE)

def safe_div(num, den):
    if den is None or den == 0 or pd.isna(den):
        return 0
    return num / den

def calcola_kpi(df):
    if df.empty:
        return df

    numeric_cols = [
        "kg_molle", "residuo_secco", "kg_polvere_reale", "kg_polvere_conforme",
        "tempo_operativo_h", "fermi_h"
    ]

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
            "threshold": {
                "line": {"color": "black", "width": 4},
                "thickness": 0.75,
                "value": 75
            }
        }
    ))
    fig.update_layout(height=330, margin=dict(l=30, r=30, t=70, b=20))
    return fig

inizializza_file()

st.title("Dashboard OEE Spray Dryer")

tab_inserimento, tab_cruscotto, tab_prodotti = st.tabs([
    "Inserimento dati",
    "Cruscotto OEE",
    "Anagrafica prodotti"
])

with tab_inserimento:
    st.subheader("Inserimento dati produzione")

    prodotti = leggi_prodotti()
    prodotti["label"] = prodotti["codice_prodotto"] + " - " + prodotti["descrizione_prodotto"]

    with st.form("inserimento_dati"):
        data = st.date_input("Data")
        turno = st.selectbox("Turno", ["1", "2", "3"])

        prodotto_label = st.selectbox(
            "Prodotto",
            prodotti["label"].tolist(),
            help="Seleziona il codice prodotto. La descrizione viene compilata automaticamente."
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

        motivazione_nc = st.text_area(
            "Motivazione NC",
            placeholder="Esempio: umidità alta, granulometria fuori specifica, colore non conforme, densità apparente bassa..."
        )

        salva = st.form_submit_button("Salva dati")

    if salva:
        nuova_riga = pd.DataFrame([{
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
            "motivazione_nc": motivazione_nc
        }])

        df_db = leggi_database()
        df_db = pd.concat([df_db, nuova_riga], ignore_index=True)
        df_db.to_csv(DATABASE, index=False)

        st.success("Dati salvati correttamente.")

with tab_cruscotto:
    df = calcola_kpi(leggi_database())

    if df.empty:
        st.info("Nessun dato ancora inserito.")
    else:
        st.subheader("Cruscotto automatico OEE")

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            prodotti_disponibili = ["Tutti"] + sorted(df["codice_prodotto"].dropna().unique().tolist())
            filtro_prodotto = st.selectbox("Filtro prodotto", prodotti_disponibili)
        with col_f2:
            turni_disponibili = ["Tutti"] + sorted(df["turno"].dropna().astype(str).unique().tolist())
            filtro_turno = st.selectbox("Filtro turno", turni_disponibili)
        with col_f3:
            periodo = st.date_input(
                "Periodo",
                value=[
                    df["data"].min().date() if not pd.isna(df["data"].min()) else pd.Timestamp.today().date(),
                    df["data"].max().date() if not pd.isna(df["data"].max()) else pd.Timestamp.today().date()
                ]
            )

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
            oee_medio = df_f["oee"].mean()
            availability = df_f["availability"].mean()
            performance = df_f["performance"].mean()
            quality = df_f["quality"].mean()
            resa = df_f["resa"].mean()

            c1, c2 = st.columns([1.2, 1])

            with c1:
                st.plotly_chart(gauge_oee(oee_medio), use_container_width=True)

            with c2:
                st.metric("Disponibilità", f"{availability:.1%}")
                st.metric("Performance", f"{performance:.1%}")
                st.metric("Qualità", f"{quality:.1%}")
                st.metric("Resa processo", f"{resa:.1%}")

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Kg molle", f"{df_f['kg_molle'].sum():.1f}")
            k2.metric("Kg polvere teorica", f"{df_f['kg_polvere_teorica'].sum():.1f}")
            k3.metric("Kg polvere reale", f"{df_f['kg_polvere_reale'].sum():.1f}")
            k4.metric("Kg NC", f"{df_f['kg_polvere_nc'].sum():.1f}")

            st.divider()

            df_trend = df_f.sort_values("data")
            fig_trend = px.line(
                df_trend,
                x="data",
                y=["oee", "availability", "performance", "quality", "resa"],
                markers=True,
                title="Trend KPI"
            )
            fig_trend.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig_trend, use_container_width=True)

            col_g1, col_g2 = st.columns(2)

            with col_g1:
                df_prod = df_f.groupby(["codice_prodotto", "descrizione_prodotto"], as_index=False)["oee"].mean()
                df_prod["prodotto"] = df_prod["codice_prodotto"] + " - " + df_prod["descrizione_prodotto"]
                fig_prod = px.bar(
                    df_prod,
                    x="prodotto",
                    y="oee",
                    title="OEE medio per prodotto"
                )
                fig_prod.update_yaxes(tickformat=".0%")
                st.plotly_chart(fig_prod, use_container_width=True)

            with col_g2:
                df_nc = df_f[df_f["kg_polvere_nc"] > 0].copy()
                if df_nc.empty:
                    st.info("Nessuna NC registrata nel periodo.")
                else:
                    df_nc["motivazione_nc"] = df_nc["motivazione_nc"].fillna("Non specificata")
                    df_nc_g = df_nc.groupby("motivazione_nc", as_index=False)["kg_polvere_nc"].sum()
                    fig_nc = px.bar(
                        df_nc_g,
                        x="motivazione_nc",
                        y="kg_polvere_nc",
                        title="NC per motivazione"
                    )
                    st.plotly_chart(fig_nc, use_container_width=True)

            st.subheader("Storico produzioni")
            st.dataframe(df_f, use_container_width=True)

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
            nuova_riga = pd.DataFrame([{
                "codice_prodotto": nuovo_codice.strip(),
                "descrizione_prodotto": nuova_descrizione.strip()
            }])
            prodotti = pd.concat([prodotti, nuova_riga], ignore_index=True)
            prodotti = prodotti.drop_duplicates(subset=["codice_prodotto"], keep="last")
            prodotti.to_csv(PRODOTTI_FILE, index=False)
            st.success("Prodotto aggiunto correttamente. Aggiorna la pagina per visualizzarlo nel menu.")
