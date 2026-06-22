import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime, time
import math

st.set_page_config(page_title="OEE Spray Dryer", layout="wide")

TURNI = {
    "1": {"inizio": time(6, 0), "fine": time(14, 0)},
    "2": {"inizio": time(14, 0), "fine": time(22, 0)},
    "3": {"inizio": time(22, 0), "fine": time(6, 0)},
}

TURNO_H = 8

EVENTI = [
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

COL_PRODUZIONI = [
    "id_lotto", "id_turno", "data", "turno", "codice_prodotto", "descrizione_prodotto",
    "lotto", "kg_molle", "residuo_secco", "kg_polvere_teorica", "kg_polvere_reale",
    "ora_inizio", "ora_fine", "ore_produzione", "stato_analisi", "kg_conformi",
    "kg_nc", "causa_nc", "note_nc", "data_rilascio_analisi"
]

COL_FERMI = [
    "id_fermo", "id_turno", "data", "turno", "ora_inizio", "ora_fine",
    "durata_h", "causale_fermo", "note_fermo"
]

COL_PRODOTTI = ["codice_prodotto", "descrizione_prodotto", "capacita_kg_h"]


def inizializza_file():
    Path("data").mkdir(parents=True, exist_ok=True)
    if not PRODOTTI_FILE.exists():
        pd.DataFrame(columns=COL_PRODOTTI).to_csv(PRODOTTI_FILE, index=False)
    if not PRODUZIONI_FILE.exists():
        pd.DataFrame(columns=COL_PRODUZIONI).to_csv(PRODUZIONI_FILE, index=False)
    if not FERMI_FILE.exists():
        pd.DataFrame(columns=COL_FERMI).to_csv(FERMI_FILE, index=False)


def leggi_csv(path, cols):
    inizializza_file()
    df = pd.read_csv(path)
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols]


def leggi_prodotti():
    df = leggi_csv(PRODOTTI_FILE, COL_PRODOTTI)
    if df.empty:
        df = pd.DataFrame([{
            "codice_prodotto": "INSERIRE",
            "descrizione_prodotto": "Inserire anagrafica prodotti",
            "capacita_kg_h": 20,
        }])
    df["capacita_kg_h"] = pd.to_numeric(df["capacita_kg_h"], errors="coerce").fillna(20)
    return df


def leggi_produzioni():
    return leggi_csv(PRODUZIONI_FILE, COL_PRODUZIONI)


def leggi_fermi():
    return leggi_csv(FERMI_FILE, COL_FERMI)


def safe_div(num, den):
    if den is None or den == 0 or pd.isna(den):
        return 0
    return num / den


def ore_da_orari(ora_inizio, ora_fine):
    dt_i = datetime.combine(datetime.today(), ora_inizio)
    dt_f = datetime.combine(datetime.today(), ora_fine)
    durata = (dt_f - dt_i).total_seconds() / 3600
    if durata < 0:
        durata += 24
    return durata


def prepara_produzioni(df):
    if df.empty:
        return df
    for c in ["kg_molle", "residuo_secco", "kg_polvere_teorica", "kg_polvere_reale", "ore_produzione", "kg_conformi", "kg_nc"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
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
    start, end = pd.to_datetime(periodo[0]), pd.to_datetime(periodo[1])
    return df[(df[col] >= start) & (df[col] <= end)]


def calcola_cruscotto(prod, fermi):
    if prod.empty:
        return {"oee":0, "disp_operativa":0, "disp_tecnica":0, "performance":0, "quality":0, "kg_molle":0, "kg_teorici":0, "kg_reali":0, "kg_nc":0, "resa":0}

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
    quality = safe_div(analizzati["kg_conformi"].sum(), analizzati["kg_polvere_reale"].sum()) if not analizzati.empty else 0

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


def reset_turno_session():
    st.session_state["eventi_turno"] = []


inizializza_file()

if "eventi_turno" not in st.session_state:
    st.session_state["eventi_turno"] = []

if "salvato" not in st.session_state:
    st.session_state["salvato"] = False

st.title("Dashboard OEE Spray Dryer - V7")

if st.session_state["salvato"]:
    st.session_state["salvato"] = False
    st.success("Turno salvato correttamente. Il modulo è stato svuotato.")

tab_turno, tab_qualita, tab_cruscotto, tab_formule, tab_prodotti, tab_gestione = st.tabs([
    "Turno",
    "Qualità",
    "Cruscotto OEE",
    "Assunzioni e formule",
    "Anagrafica prodotti",
    "Gestione dati",
])

with tab_turno:
    st.subheader("Compilazione turno")

    c0, c1 = st.columns(2)
    with c0:
        data_turno = st.date_input("Data turno")
    with c1:
        turno = st.selectbox("Turno", ["1", "2", "3"])

    st.caption(f"Turno {turno}: {TURNI[turno]['inizio'].strftime('%H:%M')} - {TURNI[turno]['fine'].strftime('%H:%M')} | Durata pianificata: 8 h")

    st.divider()
    st.markdown("### Aggiungi evento")

    prodotti = leggi_prodotti()
    prodotti["label"] = prodotti["codice_prodotto"].astype(str) + " - " + prodotti["descrizione_prodotto"].astype(str)

    with st.form("form_evento", clear_on_submit=True):
        tipo_evento = st.selectbox("Tipo evento", EVENTI)

        c2, c3 = st.columns(2)
        with c2:
            ora_inizio = st.time_input("Ora inizio evento")
        with c3:
            ora_fine = st.time_input("Ora fine evento")

        durata_h = ore_da_orari(ora_inizio, ora_fine)
        st.metric("Durata evento", f"{durata_h:.2f} h")

        evento = {
            "tipo_evento": tipo_evento,
            "ora_inizio": str(ora_inizio),
            "ora_fine": str(ora_fine),
            "durata_h": durata_h,
        }

        if tipo_evento == "Produzione":
            prodotto_label = st.selectbox("Prodotto", prodotti["label"].tolist())
            prodotto = prodotti[prodotti["label"] == prodotto_label].iloc[0]
            lotto = st.text_input("Lotto")

            p1, p2 = st.columns(2)
            with p1:
                kg_molle = st.number_input("Kg estratto molle inserito", min_value=0.0, step=1.0)
            with p2:
                residuo_secco = st.number_input("Residuo secco %", min_value=0.0, max_value=100.0, step=0.1)

            kg_teorici = kg_molle * residuo_secco / 100
            st.metric("Kg polvere teorica", f"{kg_teorici:.2f} kg")

            kg_polvere = st.number_input("Kg polvere prodotta", min_value=0.0, step=1.0)

            evento.update({
                "codice_prodotto": prodotto["codice_prodotto"],
                "descrizione_prodotto": prodotto["descrizione_prodotto"],
                "lotto": lotto,
                "kg_molle": kg_molle,
                "residuo_secco": residuo_secco,
                "kg_polvere_teorica": kg_teorici,
                "kg_polvere_reale": kg_polvere,
                "note": "",
            })
        else:
            note = st.text_area("Note evento")
            evento.update({
                "codice_prodotto": "",
                "descrizione_prodotto": "",
                "lotto": "",
                "kg_molle": 0,
                "residuo_secco": 0,
                "kg_polvere_teorica": 0,
                "kg_polvere_reale": 0,
                "note": note,
            })

        aggiungi = st.form_submit_button("Aggiungi evento al turno")

    if aggiungi:
        if durata_h <= 0:
            st.error("Controlla ora inizio e ora fine evento.")
        elif tipo_evento == "Produzione" and evento["lotto"].strip() == "":
            st.error("Per un evento di produzione devi inserire il lotto.")
        else:
            st.session_state["eventi_turno"].append(evento)
            st.rerun()

    st.divider()
    st.markdown("### Eventi inseriti nel turno")

    eventi_df = pd.DataFrame(st.session_state["eventi_turno"])

    if eventi_df.empty:
        st.info("Nessun evento inserito.")
    else:
        st.dataframe(eventi_df, use_container_width=True)

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

        if ore_produzione + ore_fermo > TURNO_H:
            st.warning("La somma degli eventi supera le 8 ore del turno.")
        elif ore_produzione + ore_fermo < TURNO_H:
            st.warning("La somma degli eventi non copre completamente le 8 ore del turno.")

        c_reset, c_save = st.columns(2)
        with c_reset:
            if st.button("Svuota eventi turno"):
                reset_turno_session()
                st.rerun()

        with c_save:
            if st.button("Salva turno"):
                id_turno = datetime.now().strftime("%Y%m%d%H%M%S")
                prod_rows = []
                fermi_rows = []

                for i, ev in enumerate(st.session_state["eventi_turno"], start=1):
                    if ev["tipo_evento"] == "Produzione" and ev["durata_h"] >= (1/60):
                        prod_rows.append({
                            "id_lotto": f"{id_turno}-P{i}",
                            "id_turno": id_turno,
                            "data": data_turno,
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
                    elif ev["tipo_evento"] != "Produzione":
                        fermi_rows.append({
                            "id_fermo": f"{id_turno}-F{i}",
                            "id_turno": id_turno,
                            "data": data_turno,
                            "turno": turno,
                            "ora_inizio": ev["ora_inizio"],
                            "ora_fine": ev["ora_fine"],
                            "durata_h": ev["durata_h"],
                            "causale_fermo": ev["tipo_evento"],
                            "note_fermo": ev["note"],
                        })

                if len(prod_rows) == 0:
                    st.error("Per salvare il turno serve almeno un evento Produzione di durata >= 1 minuto.")
                else:
                    prod = leggi_produzioni()
                    fermi = leggi_fermi()

                    if prod_rows:
                        prod = pd.concat([prod, pd.DataFrame(prod_rows)], ignore_index=True)
                        prod.to_csv(PRODUZIONI_FILE, index=False)

                    if fermi_rows:
                        fermi = pd.concat([fermi, pd.DataFrame(fermi_rows)], ignore_index=True)
                        fermi.to_csv(FERMI_FILE, index=False)

                    reset_turno_session()
                    st.session_state["salvato"] = True
                    st.rerun()

with tab_qualita:
    st.subheader("Lotti in attesa analisi")

    prod = prepara_produzioni(leggi_produzioni())
    attesa = prod[prod["stato_analisi"] == "ATTESA_ANALISI"].copy() if not prod.empty else prod

    if attesa.empty:
        st.info("Nessun lotto in attesa analisi.")
    else:
        attesa["label"] = attesa["lotto"].astype(str) + " | " + attesa["codice_prodotto"].astype(str) + " | " + attesa["data"].dt.strftime("%d/%m/%Y")
        label = st.selectbox("Seleziona lotto", attesa["label"].tolist())
        lotto_sel = attesa[attesa["label"] == label].iloc[0]

        st.write("Prodotto:", lotto_sel["descrizione_prodotto"])
        st.write("Kg prodotti:", lotto_sel["kg_polvere_reale"])

        with st.form("form_qualita"):
            esito = st.radio("Esito", ["CONFORME", "NON_CONFORME"], horizontal=True)
            if esito == "CONFORME":
                kg_conformi = float(lotto_sel["kg_polvere_reale"])
                kg_nc = 0
                causa_nc = ""
                note_nc = ""
                st.metric("Kg conformi", f"{kg_conformi:.2f}")
            else:
                kg_conformi = st.number_input("Kg conformi", min_value=0.0, max_value=float(lotto_sel["kg_polvere_reale"]), step=1.0)
                kg_nc = max(float(lotto_sel["kg_polvere_reale"]) - kg_conformi, 0)
                st.metric("Kg NC", f"{kg_nc:.2f}")
                causa_nc = st.selectbox("Causa NC", CAUSE_NC)
                note_nc = st.text_area("Note NC")
            data_rilascio = st.date_input("Data rilascio analisi")
            salva_esito = st.form_submit_button("Salva esito")

        if salva_esito:
            df = leggi_produzioni()
            mask = df["id_lotto"].astype(str) == str(lotto_sel["id_lotto"])
            df.loc[mask, "stato_analisi"] = esito
            df.loc[mask, "kg_conformi"] = kg_conformi
            df.loc[mask, "kg_nc"] = kg_nc
            df.loc[mask, "causa_nc"] = causa_nc
            df.loc[mask, "note_nc"] = note_nc
            df.loc[mask, "data_rilascio_analisi"] = data_rilascio
            df.to_csv(PRODUZIONI_FILE, index=False)
            st.session_state["salvato"] = True
            st.rerun()

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
                st.plotly_chart(px.bar(fermo_causa, x="causale_fermo", y="durata_h", title="Ore fermo per causale"), use_container_width=True)
        with g2:
            nc = prod_f[prod_f["stato_analisi"] == "NON_CONFORME"]
            if nc.empty:
                st.info("Nessuna NC.")
            else:
                nc_causa = nc.groupby("causa_nc", as_index=False)["kg_nc"].sum()
                st.plotly_chart(px.bar(nc_causa, x="causa_nc", y="kg_nc", title="Kg NC per causa"), use_container_width=True)

        st.subheader("Produzioni")
        st.dataframe(prod_f, use_container_width=True)

with tab_formule:
    st.subheader("Assunzioni e formule")
    st.markdown("""
### Logica operativa V7
L'operatore compila un solo **turno** aggiungendo eventi in sequenza.  
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

La capacità nominale prodotto è gestita in **Anagrafica prodotti**. Default: **20 kg/h**.

### Qualità
La qualità considera solo i lotti già rilasciati dal laboratorio.

`qualità = kg conformi / kg prodotti analizzati`

### OEE
`OEE = disponibilità operativa × performance × qualità`
""")

with tab_prodotti:
    st.subheader("Anagrafica prodotti")
    prodotti = leggi_prodotti()
    st.dataframe(prodotti, use_container_width=True)

    with st.form("form_prodotto"):
        codice = st.text_input("Codice prodotto")
        descrizione = st.text_input("Descrizione prodotto")
        capacita = st.number_input("Capacità nominale kg/h", min_value=0.0, value=20.0, step=1.0)
        salva_prod = st.form_submit_button("Salva prodotto")

    if salva_prod:
        if codice.strip() == "" or descrizione.strip() == "":
            st.error("Inserisci codice e descrizione.")
        else:
            nuovo = pd.DataFrame([{
                "codice_prodotto": codice.strip(),
                "descrizione_prodotto": descrizione.strip(),
                "capacita_kg_h": capacita,
            }])
            prodotti = pd.concat([prodotti, nuovo], ignore_index=True).drop_duplicates(subset=["codice_prodotto"], keep="last")
            prodotti.to_csv(PRODOTTI_FILE, index=False)
            st.session_state["salvato"] = True
            st.rerun()

with tab_gestione:
    st.subheader("Gestione dati")

    st.markdown("### Produzioni")
    prod = leggi_produzioni()
    st.dataframe(prod, use_container_width=True)
    if not prod.empty:
        id_lotto = st.selectbox("Produzione da eliminare", prod["id_lotto"].astype(str).tolist())
        if st.button("Elimina produzione selezionata"):
            prod = prod[prod["id_lotto"].astype(str) != str(id_lotto)]
            prod.to_csv(PRODUZIONI_FILE, index=False)
            st.session_state["salvato"] = True
            st.rerun()

    st.markdown("### Fermi")
    fermi = leggi_fermi()
    st.dataframe(fermi, use_container_width=True)
    if not fermi.empty:
        id_fermo = st.selectbox("Fermo da eliminare", fermi["id_fermo"].astype(str).tolist())
        if st.button("Elimina fermo selezionato"):
            fermi = fermi[fermi["id_fermo"].astype(str) != str(id_fermo)]
            fermi.to_csv(FERMI_FILE, index=False)
            st.session_state["salvato"] = True
            st.rerun()

    st.divider()
    if st.button("Cancella tutto lo storico produzioni"):
        pd.DataFrame(columns=COL_PRODUZIONI).to_csv(PRODUZIONI_FILE, index=False)
        st.session_state["salvato"] = True
        st.rerun()

    if st.button("Cancella tutto lo storico fermi"):
        pd.DataFrame(columns=COL_FERMI).to_csv(FERMI_FILE, index=False)
        st.session_state["salvato"] = True
        st.rerun()
