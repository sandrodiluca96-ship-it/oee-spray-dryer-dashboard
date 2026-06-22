import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="OEE Spray Dryer", layout="wide")

DATABASE = Path("data/database.csv")
CAPACITA_MACCHINA_KG_H = 20

st.title("Dashboard OEE Spray Dryer")

with st.form("inserimento_dati"):
    st.subheader("Inserimento dati produzione")

    data = st.date_input("Data")
    turno = st.selectbox("Turno", ["1", "2", "3"])
    prodotto = st.text_input("Prodotto")
    lotto = st.text_input("Lotto")

    kg_molle = st.number_input("Kg estratto molle inserito", min_value=0.0, step=1.0)
    residuo_secco = st.number_input("Residuo secco %", min_value=0.0, max_value=100.0, step=0.1)

    kg_polvere_teorica = kg_molle * residuo_secco / 100
    st.metric("Polvere teorica calcolata", f"{kg_polvere_teorica:.2f} kg")

    kg_polvere_reale = st.number_input("Kg polvere reale prodotta", min_value=0.0, step=1.0)
    kg_polvere_conforme = st.number_input("Kg polvere conforme", min_value=0.0, step=1.0)

    tempo_operativo_h = st.number_input("Ore operative", min_value=0.0, step=0.5)
    fermi_h = st.number_input("Ore fermo", min_value=0.0, step=0.5)

    motivazione_nc = st.text_area("Motivazione NC")

    salva = st.form_submit_button("Salva dati")

if salva:
    nuova_riga = pd.DataFrame([{
        "data": data,
        "turno": turno,
        "prodotto": prodotto,
        "lotto": lotto,
        "kg_molle": kg_molle,
        "residuo_secco": residuo_secco,
        "kg_polvere_reale": kg_polvere_reale,
        "kg_polvere_conforme": kg_polvere_conforme,
        "tempo_operativo_h": tempo_operativo_h,
        "fermi_h": fermi_h,
        "motivazione_nc": motivazione_nc
    }])

    df = pd.read_csv(DATABASE)
    df = pd.concat([df, nuova_riga], ignore_index=True)
    df.to_csv(DATABASE, index=False)

    st.success("Dati salvati correttamente.")

df = pd.read_csv(DATABASE)

if not df.empty:
    df["kg_polvere_teorica"] = df["kg_molle"] * df["residuo_secco"] / 100
    df["resa"] = df["kg_polvere_reale"] / df["kg_polvere_teorica"]
    df["performance"] = df["kg_polvere_reale"] / (CAPACITA_MACCHINA_KG_H * df["tempo_operativo_h"])
    df["quality"] = df["kg_polvere_conforme"] / df["kg_polvere_reale"]
    df["availability"] = df["tempo_operativo_h"] / (df["tempo_operativo_h"] + df["fermi_h"])
    df["oee"] = df["availability"] * df["performance"] * df["quality"]

    st.dataframe(df, use_container_width=True)
else:
    st.info("Nessun dato ancora inserito.")
