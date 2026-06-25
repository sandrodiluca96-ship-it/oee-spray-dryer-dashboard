import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime, time
from io import BytesIO

st.set_page_config(page_title="OEE Spray Dryer", layout="wide")

# ============================================================
# STILE
# ============================================================

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
.small-muted {
    color: #777;
    font-size: 0.9rem;
}
.required-box {
    background-color: #FFF8CC;
    border-left: 6px solid #FFC107;
    padding: 10px 14px;
    border-radius: 6px;
    color: #4E342E;
    font-weight: 600;
    margin-bottom: 8px;
}
.required-ok {
    background-color: #E8F5E9;
    border-left: 6px solid #2E7D32;
    padding: 10px 14px;
    border-radius: 6px;
    color: #1B5E20;
    font-weight: 600;
    margin-bottom: 8px;
}
.field-status-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin-bottom: 12px;
}
.status-yellow {
    background-color: #FFF8CC;
    border: 2px solid #FFC107;
    border-left: 8px solid #FFC107;
    border-radius: 8px;
    padding: 10px 12px;
    font-weight: 700;
    color: #4E342E;
}
.status-green {
    background-color: #E8F5E9;
    border: 2px solid #2E7D32;
    border-left: 8px solid #2E7D32;
    border-radius: 8px;
    padding: 10px 12px;
    font-weight: 700;
    color: #1B5E20;
}
.status-title {
    font-size: 0.85rem;
    opacity: 0.85;
}
.status-value {
    font-size: 1rem;
    margin-top: 2px;
}

/* Campi Streamlit: giallo come default operativo */
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stDateInput"] input,
div[data-testid="stTimeInput"] input,
div[data-baseweb="select"] > div {
    background-color: #FFF8CC !important;
    border: 2px solid #FFC107 !important;
    color: inherit !important;
}

/* Quando un campo testuale contiene un valore, diventa verde. */
div[data-testid="stTextInput"] input:not(:placeholder-shown),
div[data-testid="stDateInput"] input:not(:placeholder-shown),
div[data-testid="stTimeInput"] input:not(:placeholder-shown) {
    background-color: #E8F5E9 !important;
    border: 2px solid #2E7D32 !important;
}

/* Note sempre bianche */
div[data-testid="stTextArea"] textarea {
    background-color: #FFFFFF !important;
    border: 1px solid #757575 !important;
}

label p {
    font-weight: 700 !important;
}


/* Testo sempre nero e leggibile SOLO nei campi colorati */
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stDateInput"] input,
div[data-testid="stTimeInput"] input,
div[data-baseweb="select"] > div,
div[data-baseweb="select"] span,
div[data-baseweb="select"] input {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}

/* Placeholder leggibile nei campi colorati */
div[data-testid="stTextInput"] input::placeholder,
div[data-testid="stNumberInput"] input::placeholder,
div[data-testid="stDateInput"] input::placeholder,
div[data-testid="stTimeInput"] input::placeholder,
div[data-baseweb="select"] input::placeholder {
    color: #333333 !important;
    opacity: 1 !important;
}

/* Icone e controlli interni dei campi colorati */
div[data-testid="stNumberInput"] button,
div[data-testid="stDateInput"] button,
div[data-testid="stTimeInput"] button,
div[data-baseweb="select"] svg {
    color: #000000 !important;
    fill: #000000 !important;
}

/* Menu a tendina: opzioni leggibili */
div[role="listbox"],
div[role="option"] {
    color: #000000 !important;
    background-color: #FFFFFF !important;
}

/* Note e textarea: restano bianche ma testo nero */
div[data-testid="stTextArea"] textarea {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}


/* Release 3.0 - campi controllati */
.r3-field-yellow {
    background-color: #FFF8CC;
    border: 2px solid #FFC107;
    border-radius: 10px;
    padding: 10px 12px 4px 12px;
    margin-bottom: 10px;
}
.r3-field-green {
    background-color: #E8F5E9;
    border: 2px solid #2E7D32;
    border-radius: 10px;
    padding: 10px 12px 4px 12px;
    margin-bottom: 10px;
}
.r3-field-red {
    background-color: #FFEBEE;
    border: 2px solid #C62828;
    border-radius: 10px;
    padding: 10px 12px 4px 12px;
    margin-bottom: 10px;
}
.r3-field-white {
    background-color: #FFFFFF;
    border: 1px solid #BDBDBD;
    border-radius: 10px;
    padding: 10px 12px 4px 12px;
    margin-bottom: 10px;
}
.r3-field-title {
    font-weight: 800;
    color: #000000;
    margin-bottom: 4px;
}
.r3-field-yellow input,
.r3-field-green input,
.r3-field-red input,
.r3-field-white input,
.r3-field-yellow textarea,
.r3-field-green textarea,
.r3-field-red textarea,
.r3-field-white textarea {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}
.r3-field-yellow div[data-baseweb="select"] span,
.r3-field-green div[data-baseweb="select"] span,
.r3-field-red div[data-baseweb="select"] span,
.r3-field-white div[data-baseweb="select"] span {
    color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONFIGURAZIONE
# ============================================================

ADMIN_PASSWORD = "EVRA26%"
STANDARD_ESTRATTO_PURO = 0.40
TURNO_H = 8

TURNI = {
    "1": {"inizio": time(6, 0), "fine": time(14, 0)},
    "2": {"inizio": time(14, 0), "fine": time(22, 0)},
    "3": {"inizio": time(22, 0), "fine": time(6, 0)},
}

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

TIPI_PRODUZIONE = [
    "Apertura lotto",
    "Prosecuzione lotto",
    "Chiusura lotto",
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

DATA_DIR = Path("data")
ASSETS_DIR = Path("assets")

PRODOTTI_FILE = DATA_DIR / "prodotti.csv"
EVENTI_FILE = DATA_DIR / "eventi_turno.csv"
LOTTI_FILE = DATA_DIR / "lotti.csv"

COL_PRODOTTI = [
    "codice_prodotto",
    "descrizione_prodotto",
    "capacita_kg_h",
]

COL_EVENTI = [
    "id_evento",
    "id_turno",
    "data",
    "turno",
    "tipo_evento",
    "tipo_produzione",
    "lotto_molle",
    "codice_prodotto",
    "descrizione_prodotto",
    "ora_inizio",
    "ora_fine",
    "durata_h",
    "kg_molle",
    "residuo_secco",
    "kg_secco_puro",
    "kg_maltodestrina",
    "kg_polvere_teorica",
    "taglio_maltodestrina_pct",
    "estratto_puro_pct",
    "kg_polvere_finale",
    "kg_equivalenti_standard",
    "note",
]

COL_LOTTI = [
    "lotto_molle",
    "codice_prodotto",
    "descrizione_prodotto",
    "data_apertura",
    "data_chiusura",
    "stato_lotto",
    "kg_molle",
    "residuo_secco",
    "kg_secco_puro",
    "kg_maltodestrina",
    "kg_polvere_teorica",
    "taglio_maltodestrina_pct",
    "estratto_puro_pct",
    "kg_polvere_finale",
    "kg_equivalenti_standard",
    "ore_produzione_totali",
    "resa_fisica",
    "resa_equivalente",
    "stato_analisi",
    "kg_conformi",
    "kg_nc",
    "causa_nc",
    "note_nc",
    "data_rilascio_analisi",
]

# ============================================================
# FUNZIONI DATI
# ============================================================

def inizializza_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not PRODOTTI_FILE.exists():
        pd.DataFrame(columns=COL_PRODOTTI).to_csv(PRODOTTI_FILE, index=False)

    if not EVENTI_FILE.exists():
        pd.DataFrame(columns=COL_EVENTI).to_csv(EVENTI_FILE, index=False)

    if not LOTTI_FILE.exists():
        pd.DataFrame(columns=COL_LOTTI).to_csv(LOTTI_FILE, index=False)


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


def leggi_prodotti():
    df = leggi_csv(PRODOTTI_FILE, COL_PRODOTTI)

    if df.empty:
        df = pd.DataFrame([{
            "codice_prodotto": "INSERIRE",
            "descrizione_prodotto": "Inserire anagrafica prodotto",
            "capacita_kg_h": "20",
        }])

    df["capacita_kg_h"] = pd.to_numeric(df["capacita_kg_h"], errors="coerce").fillna(20)
    return df


def leggi_eventi():
    return leggi_csv(EVENTI_FILE, COL_EVENTI)


def leggi_lotti():
    return leggi_csv(LOTTI_FILE, COL_LOTTI)


def safe_float(value, default=0.0):
    val = pd.to_numeric(value, errors="coerce")
    if pd.isna(val):
        return default
    return float(val)


def safe_div(num, den):
    try:
        if den is None or den == 0 or pd.isna(den):
            return 0
        return num / den
    except Exception:
        return 0


def nuovo_id():
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


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


def parse_time_manual(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        return datetime.strptime(str(value).strip(), "%H:%M").time()
    except Exception:
        return None


def parse_date_manual(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        # supporta gg/mm/aaaa e aaaa-mm-gg
        txt = str(value).strip()
        if "/" in txt:
            return datetime.strptime(txt, "%d/%m/%Y").date()
        return datetime.strptime(txt, "%Y-%m-%d").date()
    except Exception:
        return None


def field_box_start(label, status="yellow"):
    cls = {
        "green": "r3-field-green",
        "yellow": "r3-field-yellow",
        "red": "r3-field-red",
        "white": "r3-field-white",
    }.get(status, "r3-field-yellow")
    icon = {"green": "🟢", "yellow": "🟡", "red": "🔴", "white": "⚪"}.get(status, "🟡")
    st.markdown(f"<div class='{cls}'><div class='r3-field-title'>{icon} {label}</div>", unsafe_allow_html=True)


def field_box_end():
    st.markdown("</div>", unsafe_allow_html=True)


def text_field(label, key, value="", required=True, validator=None, placeholder=""):
    current = st.session_state.get(key, value)
    ok = False
    if validator:
        ok = validator(current)
    else:
        ok = str(current).strip() != ""

    status = "green" if ok else ("yellow" if required else "white")
    field_box_start(label, status)
    result = st.text_input(label, value=current, key=key, placeholder=placeholder, label_visibility="collapsed")
    field_box_end()
    return result, ok


def note_field(label, key, value=""):
    field_box_start(label, "white")
    result = st.text_area(label, value=st.session_state.get(key, value), key=key, label_visibility="collapsed")
    field_box_end()
    return result


def select_field(label, options, key, required=True, placeholder="Seleziona"):
    current = st.session_state.get(key, None)
    idx = None
    if current in options:
        idx = options.index(current)

    ok = current in options and current not in ["", None, "-- Seleziona prodotto --", "-- Inserisci manualmente --"]
    status = "green" if ok else ("yellow" if required else "white")
    field_box_start(label, status)
    result = st.selectbox(label, options, index=idx, key=key, placeholder=placeholder, label_visibility="collapsed")
    field_box_end()
    return result, ok


def float_field(label, key, value="", required=True, min_value=None, max_value=None, placeholder=""):
    def validator(v):
        try:
            if str(v).strip() == "":
                return False
            f = float(str(v).replace(",", "."))
            if min_value is not None and f < min_value:
                return False
            if max_value is not None and f > max_value:
                return False
            return True
        except Exception:
            return False

    txt, ok = text_field(label, key, value=value, required=required, validator=validator, placeholder=placeholder)
    val = safe_float(str(txt).replace(",", "."), 0)
    return val, ok


def time_field(label, key, value="", required=True):
    txt, ok = text_field(label, key, value=value, required=required, validator=lambda v: parse_time_manual(v) is not None, placeholder="HH:MM")
    return parse_time_manual(txt), ok


def date_field(label, key, value="", required=True):
    txt, ok = text_field(label, key, value=value, required=required, validator=lambda v: parse_date_manual(v) is not None, placeholder="gg/mm/aaaa")
    return parse_date_manual(txt), ok


def calcola_miscele(kg_molle, residuo_secco, kg_maltodestrina, kg_polvere_finale=None):
    kg_secco_puro = kg_molle * residuo_secco / 100
    kg_polvere_teorica = kg_secco_puro + kg_maltodestrina
    taglio_malto_pct = safe_div(kg_maltodestrina, kg_polvere_teorica) * 100
    estratto_puro_pct = safe_div(kg_secco_puro, kg_polvere_teorica) * 100

    if kg_polvere_finale is None or kg_polvere_finale == "":
        kg_equivalenti = 0
    else:
        kg_equivalenti = safe_float(kg_polvere_finale) * safe_div((estratto_puro_pct / 100), STANDARD_ESTRATTO_PURO)

    return {
        "kg_secco_puro": kg_secco_puro,
        "kg_polvere_teorica": kg_polvere_teorica,
        "taglio_maltodestrina_pct": taglio_malto_pct,
        "estratto_puro_pct": estratto_puro_pct,
        "kg_equivalenti_standard": kg_equivalenti,
    }


def prepara_eventi(df):
    if df.empty:
        return df

    for col in [
        "durata_h",
        "kg_molle",
        "residuo_secco",
        "kg_secco_puro",
        "kg_maltodestrina",
        "kg_polvere_teorica",
        "taglio_maltodestrina_pct",
        "estratto_puro_pct",
        "kg_polvere_finale",
        "kg_equivalenti_standard",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    return df


def prepara_lotti(df):
    if df.empty:
        return df

    for col in [
        "kg_molle",
        "residuo_secco",
        "kg_secco_puro",
        "kg_maltodestrina",
        "kg_polvere_teorica",
        "taglio_maltodestrina_pct",
        "estratto_puro_pct",
        "kg_polvere_finale",
        "kg_equivalenti_standard",
        "ore_produzione_totali",
        "resa_fisica",
        "resa_equivalente",
        "kg_conformi",
        "kg_nc",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["data_apertura"] = pd.to_datetime(df["data_apertura"], errors="coerce")
    df["data_chiusura"] = pd.to_datetime(df["data_chiusura"], errors="coerce")
    return df


def aggiorna_lotti_da_eventi():
    eventi = prepara_eventi(leggi_eventi())
    lotti = leggi_lotti()

    if eventi.empty:
        return

    prod_events = eventi[eventi["tipo_evento"] == "Produzione"].copy()

    if prod_events.empty:
        return

    rows = []

    for lotto, grp in prod_events.groupby("lotto_molle"):
        if str(lotto).strip() == "":
            continue

        aperture = grp[grp["tipo_produzione"] == "Apertura lotto"]
        chiusure = grp[grp["tipo_produzione"] == "Chiusura lotto"]

        if not aperture.empty:
            ap = aperture.iloc[0]
            codice = ap["codice_prodotto"]
            descr = ap["descrizione_prodotto"]
            kg_molle = ap["kg_molle"]
            rs = ap["residuo_secco"]
            kg_puro = ap["kg_secco_puro"]
            kg_malto = ap["kg_maltodestrina"]
            kg_teorica = ap["kg_polvere_teorica"]
            taglio = ap["taglio_maltodestrina_pct"]
            estratto = ap["estratto_puro_pct"]
            data_apertura = ap["data"]
        else:
            codice = grp.iloc[0]["codice_prodotto"]
            descr = grp.iloc[0]["descrizione_prodotto"]
            kg_molle = 0
            rs = 0
            kg_puro = 0
            kg_malto = 0
            kg_teorica = 0
            taglio = 0
            estratto = 0
            data_apertura = grp["data"].min()

        if not chiusure.empty:
            ch = chiusure.iloc[-1]
            kg_finale = ch["kg_polvere_finale"]
            data_chiusura = ch["data"]
            kg_equiv = ch["kg_equivalenti_standard"]

            if kg_equiv == 0 and estratto > 0:
                kg_equiv = kg_finale * safe_div((estratto / 100), STANDARD_ESTRATTO_PURO)

            stato_lotto = "CHIUSO"
            stato_analisi = "ATTESA_ANALISI"
        else:
            kg_finale = 0
            data_chiusura = ""
            kg_equiv = 0
            stato_lotto = "APERTO"
            stato_analisi = "NON_APPLICABILE"

        ore_totali = grp["durata_h"].sum()
        resa_fisica = safe_div(kg_finale, kg_teorica)
        resa_equiv = safe_div(kg_equiv, kg_teorica)

        # Mantiene eventuale esito qualità già registrato
        existing = lotti[lotti["lotto_molle"].astype(str) == str(lotto)] if not lotti.empty else pd.DataFrame()
        if not existing.empty and str(existing.iloc[0].get("stato_analisi", "")) in ["CONFORME", "NON_CONFORME"]:
            stato_analisi = existing.iloc[0]["stato_analisi"]
            kg_conformi = existing.iloc[0].get("kg_conformi", 0)
            kg_nc = existing.iloc[0].get("kg_nc", 0)
            causa_nc = existing.iloc[0].get("causa_nc", "")
            note_nc = existing.iloc[0].get("note_nc", "")
            data_rilascio = existing.iloc[0].get("data_rilascio_analisi", "")
        else:
            kg_conformi = 0
            kg_nc = 0
            causa_nc = ""
            note_nc = ""
            data_rilascio = ""

        rows.append({
            "lotto_molle": lotto,
            "codice_prodotto": codice,
            "descrizione_prodotto": descr,
            "data_apertura": data_apertura,
            "data_chiusura": data_chiusura,
            "stato_lotto": stato_lotto,
            "kg_molle": kg_molle,
            "residuo_secco": rs,
            "kg_secco_puro": kg_puro,
            "kg_maltodestrina": kg_malto,
            "kg_polvere_teorica": kg_teorica,
            "taglio_maltodestrina_pct": taglio,
            "estratto_puro_pct": estratto,
            "kg_polvere_finale": kg_finale,
            "kg_equivalenti_standard": kg_equiv,
            "ore_produzione_totali": ore_totali,
            "resa_fisica": resa_fisica,
            "resa_equivalente": resa_equiv,
            "stato_analisi": stato_analisi,
            "kg_conformi": kg_conformi,
            "kg_nc": kg_nc,
            "causa_nc": causa_nc,
            "note_nc": note_nc,
            "data_rilascio_analisi": data_rilascio,
        })

    out = pd.DataFrame(rows)
    salva_csv(out, LOTTI_FILE, COL_LOTTI)


def crea_excel_completo():
    eventi = leggi_eventi()
    lotti = leggi_lotti()
    prodotti = leggi_prodotti()

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        eventi.to_excel(writer, sheet_name="Eventi turno", index=False)
        lotti.to_excel(writer, sheet_name="Lotti", index=False)
        prodotti.to_excel(writer, sheet_name="Prodotti", index=False)

        # Foglio sintetico
        eventi_p = prepara_eventi(eventi.copy())
        lotti_p = prepara_lotti(lotti.copy())

        sintesi = pd.DataFrame([{
            "kg_fisici": lotti_p["kg_polvere_finale"].sum() if not lotti_p.empty else 0,
            "kg_equivalenti_standard_40": lotti_p["kg_equivalenti_standard"].sum() if not lotti_p.empty else 0,
            "lotti_totali": len(lotti_p),
            "lotti_aperti": len(lotti_p[lotti_p["stato_lotto"] == "APERTO"]) if not lotti_p.empty else 0,
            "lotti_attesa_analisi": len(lotti_p[lotti_p["stato_analisi"] == "ATTESA_ANALISI"]) if not lotti_p.empty else 0,
        }])
        sintesi.to_excel(writer, sheet_name="Sintesi", index=False)

    output.seek(0)
    return output


def box_campo(nome, compilato):
    if compilato:
        st.markdown(
            f"<div class='required-ok'>✓ {nome} compilato</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='required-box'>⚠ {nome} da compilare</div>",
            unsafe_allow_html=True
        )


def status_card(label, value, compilato):
    classe = "status-green" if compilato else "status-yellow"
    icona = "🟢" if compilato else "🟡"
    valore = value if value not in [None, ""] else "Da compilare"
    st.markdown(
        f"""
        <div class="{classe}">
            <div class="status-title">{icona} {label}</div>
            <div class="status-value">{valore}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def avanzamento_compilazione(stati):
    if not stati:
        return
    completati = sum(1 for stato in stati if stato)
    totale = len(stati)
    avanzamento = completati / totale
    st.progress(avanzamento)
    st.caption(f"Avanzamento compilazione: {completati}/{totale} campi obbligatori completati")


def controlla_campi_obbligatori(tipo_evento, evento):
    mancanti = []

    if evento.get("durata_h", 0) <= 0:
        mancanti.append("orario inizio/fine evento valido")

    if tipo_evento == "Produzione":
        if str(evento.get("lotto_molle", "")).strip() == "":
            mancanti.append("lotto molle")

        if evento.get("tipo_produzione") == "Apertura lotto":
            if str(evento.get("codice_prodotto", "")).strip() == "":
                mancanti.append("prodotto")
            if safe_float(evento.get("kg_molle")) <= 0:
                mancanti.append("kg molle")
            if safe_float(evento.get("residuo_secco")) <= 0:
                mancanti.append("residuo secco %")
            if safe_float(evento.get("kg_maltodestrina")) < 0:
                mancanti.append("kg maltodestrina")

        if evento.get("tipo_produzione") == "Chiusura lotto":
            if safe_float(evento.get("kg_polvere_finale")) <= 0:
                mancanti.append("kg polvere finale")

    return mancanti


def importa_excel(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)

    imported = {}

    if "Eventi turno" in xls.sheet_names:
        ev = pd.read_excel(xls, sheet_name="Eventi turno", dtype=str).fillna("")
        imported["eventi"] = ev

    if "Lotti" in xls.sheet_names:
        lo = pd.read_excel(xls, sheet_name="Lotti", dtype=str).fillna("")
        imported["lotti"] = lo

    if "Prodotti" in xls.sheet_names:
        pr = pd.read_excel(xls, sheet_name="Prodotti", dtype=str).fillna("")
        imported["prodotti"] = pr

    return imported


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


def calcola_kpi(eventi, lotti):
    eventi = prepara_eventi(eventi.copy())
    lotti = prepara_lotti(lotti.copy())

    if eventi.empty:
        return {
            "availability": 0, "availability_technical": 0, "performance_eq": 0,
            "quality": 0, "oee": 0, "kg_fisici": 0, "kg_equiv": 0,
            "kg_puro": 0, "taglio_medio": 0,
        }

    turni = eventi[["data", "turno"]].drop_duplicates().shape[0]
    tempo_pianificato = turni * TURNO_H

    fermi = eventi[eventi["tipo_evento"] != "Produzione"].copy()
    ore_fermo = fermi["durata_h"].sum() if not fermi.empty else 0
    ore_fermo_tecnico = fermi[fermi["tipo_evento"].isin(CAUSALI_TECNICHE)]["durata_h"].sum() if not fermi.empty else 0

    availability = max(0, safe_div(tempo_pianificato - ore_fermo, tempo_pianificato))
    availability_technical = max(0, safe_div(tempo_pianificato - ore_fermo_tecnico, tempo_pianificato))

    lotti_chiusi = lotti[lotti["stato_lotto"] == "CHIUSO"].copy()
    kg_equiv = lotti_chiusi["kg_equivalenti_standard"].sum() if not lotti_chiusi.empty else 0
    kg_fisici = lotti_chiusi["kg_polvere_finale"].sum() if not lotti_chiusi.empty else 0
    kg_puro = lotti_chiusi["kg_secco_puro"].sum() if not lotti_chiusi.empty else 0
    ore_prod = lotti_chiusi["ore_produzione_totali"].sum() if not lotti_chiusi.empty else 0

    # Capacità media: per semplicità usa capacità prodotto sui lotti chiusi
    prodotti = leggi_prodotti()[["codice_prodotto", "capacita_kg_h"]]
    lotti_cap = lotti_chiusi.merge(prodotti, on="codice_prodotto", how="left") if not lotti_chiusi.empty else lotti_chiusi
    if not lotti_cap.empty:
        lotti_cap["capacita_kg_h"] = pd.to_numeric(lotti_cap["capacita_kg_h"], errors="coerce").fillna(20)
        denominatore = (lotti_cap["capacita_kg_h"] * lotti_cap["ore_produzione_totali"]).sum()
    else:
        denominatore = 0

    performance_eq = safe_div(kg_equiv, denominatore)

    analizzati = lotti[lotti["stato_analisi"].isin(["CONFORME", "NON_CONFORME"])].copy()
    quality = safe_div(analizzati["kg_conformi"].sum(), analizzati["kg_polvere_finale"].sum()) if not analizzati.empty else 0

    oee = availability * performance_eq * quality

    taglio_medio = safe_div(
        (lotti_chiusi["taglio_maltodestrina_pct"] * lotti_chiusi["kg_polvere_finale"]).sum(),
        lotti_chiusi["kg_polvere_finale"].sum()
    ) if not lotti_chiusi.empty else 0

    return {
        "availability": availability,
        "availability_technical": availability_technical,
        "performance_eq": performance_eq,
        "quality": quality,
        "oee": oee,
        "kg_fisici": kg_fisici,
        "kg_equiv": kg_equiv,
        "kg_puro": kg_puro,
        "taglio_medio": taglio_medio,
    }

# ============================================================
# SESSIONE
# ============================================================

inizializza_file()
aggiorna_lotti_da_eventi()

if "eventi_turno_buffer" not in st.session_state:
    st.session_state["eventi_turno_buffer"] = []

if "evento_da_modificare" not in st.session_state:
    st.session_state["evento_da_modificare"] = None

if "salvato" not in st.session_state:
    st.session_state["salvato"] = False


def reset_buffer():
    st.session_state["eventi_turno_buffer"] = []
    st.session_state["evento_da_modificare"] = None

# ============================================================
# APP
# ============================================================

st.title("⚙️ Dashboard OEE Spray Dryer")

if st.session_state["salvato"]:
    st.session_state["salvato"] = False
    st.success("Operazione salvata correttamente.")

tab_turno, tab_lotti, tab_qualita, tab_cruscotto, tab_formule, tab_prodotti, tab_gestione = st.tabs([
    "Turno",
    "Lotti in corso",
    "Qualità",
    "Cruscotto OEE",
    "Assunzioni e formule",
    "Anagrafica prodotti",
    "Gestione dati",
])

# ============================================================
# TURNO
# ============================================================

with tab_turno:
    st.subheader("🧭 Compilazione turno guidata - Release 3.0")

    st.caption("I campi obbligatori sono gialli. Quando il valore è valido diventano verdi. Le note restano bianche.")

    c0, c1 = st.columns(2)
    with c0:
        data_turno, data_ok = date_field("Data turno *", "r3_data_turno", required=True)
    with c1:
        turno, turno_ok = select_field("Turno *", ["1", "2", "3"], "r3_turno", required=True)

    if turno_ok:
        st.caption(
            f"Turno {turno}: {TURNI[turno]['inizio'].strftime('%H:%M')} - "
            f"{TURNI[turno]['fine'].strftime('%H:%M')} | Durata pianificata: 8 h"
        )
    else:
        st.caption("Seleziona il turno per impostare gli orari di riferimento.")

    st.divider()
    st.markdown("### ➕ Aggiungi evento")

    prodotti = leggi_prodotti()
    prodotti["label"] = prodotti["codice_prodotto"].astype(str) + " - " + prodotti["descrizione_prodotto"].astype(str)

    idx_mod = st.session_state["evento_da_modificare"]
    evento_mod = None
    if idx_mod is not None and 0 <= idx_mod < len(st.session_state["eventi_turno_buffer"]):
        evento_mod = st.session_state["eventi_turno_buffer"][idx_mod]
        st.info(f"Modifica attiva: evento {idx_mod + 1} - {evento_mod['tipo_evento']}")

    # Precarica campi in modifica
    if evento_mod:
        st.session_state["r3_tipo_evento"] = evento_mod.get("tipo_evento", "Produzione")
        st.session_state["r3_tipo_produzione"] = evento_mod.get("tipo_produzione", "Apertura lotto")
        st.session_state["r3_ora_inizio"] = str(evento_mod.get("ora_inizio", ""))[:5]
        st.session_state["r3_ora_fine"] = str(evento_mod.get("ora_fine", ""))[:5]
        st.session_state["r3_lotto_molle"] = evento_mod.get("lotto_molle", "")
        st.session_state["r3_kg_molle"] = str(evento_mod.get("kg_molle", ""))
        st.session_state["r3_rs"] = str(evento_mod.get("residuo_secco", ""))
        st.session_state["r3_malto"] = str(evento_mod.get("kg_maltodestrina", ""))
        st.session_state["r3_kg_finale"] = str(evento_mod.get("kg_polvere_finale", ""))
        st.session_state["r3_note"] = evento_mod.get("note", "")

    tipo_evento, tipo_evento_ok = select_field("Tipo evento *", TIPI_EVENTO, "r3_tipo_evento", required=True)

    ora_inizio_default = TURNI[turno]["inizio"].strftime("%H:%M") if turno_ok else "06:00"
    ora_fine_default = TURNI[turno]["fine"].strftime("%H:%M") if turno_ok else "14:00"

    if "r3_ora_inizio" not in st.session_state:
        st.session_state["r3_ora_inizio"] = ora_inizio_default
    if "r3_ora_fine" not in st.session_state:
        st.session_state["r3_ora_fine"] = ora_fine_default

    co1, co2 = st.columns(2)
    with co1:
        ora_inizio, ora_i_ok = time_field("Ora inizio evento *", "r3_ora_inizio", required=True)
    with co2:
        ora_fine, ora_f_ok = time_field("Ora fine evento *", "r3_ora_fine", required=True)

    durata_h = ore_da_orari(ora_inizio, ora_fine) if ora_i_ok and ora_f_ok else 0
    st.metric("Durata evento", f"{durata_h:.2f} h")

    evento = {
        "tipo_evento": tipo_evento if tipo_evento_ok else "",
        "tipo_produzione": "",
        "lotto_molle": "",
        "codice_prodotto": "",
        "descrizione_prodotto": "",
        "ora_inizio": str(ora_inizio) if ora_inizio else "",
        "ora_fine": str(ora_fine) if ora_fine else "",
        "durata_h": durata_h,
        "kg_molle": 0.0,
        "residuo_secco": 0.0,
        "kg_secco_puro": 0.0,
        "kg_maltodestrina": 0.0,
        "kg_polvere_teorica": 0.0,
        "taglio_maltodestrina_pct": 0.0,
        "estratto_puro_pct": 0.0,
        "kg_polvere_finale": 0.0,
        "kg_equivalenti_standard": 0.0,
        "note": "",
    }

    if tipo_evento == "Produzione":
        tipo_produzione, tipo_prod_ok = select_field("Tipo produzione *", TIPI_PRODUZIONE, "r3_tipo_produzione", required=True)

        evento["tipo_produzione"] = tipo_produzione if tipo_prod_ok else ""

        if tipo_produzione == "Apertura lotto":
            lotto_molle, lotto_ok = text_field("Lotto molle *", "r3_lotto_molle", required=True)

            labels = prodotti["label"].tolist()
            product_options = ["-- Seleziona prodotto --"] + labels
            prodotto_label, prodotto_ok = select_field(
                "Prodotto *",
                product_options,
                "r3_prodotto",
                required=True,
                placeholder="Scrivi codice o descrizione"
            )

            prodotto = None if prodotto_label == "-- Seleziona prodotto --" or prodotto_label is None else prodotti[prodotti["label"] == prodotto_label].iloc[0]

            p1, p2, p3 = st.columns(3)
            with p1:
                kg_molle, kg_molle_ok = float_field("Kg molle *", "r3_kg_molle", required=True, min_value=0.0001)
            with p2:
                residuo_secco, rs_ok = float_field("Residuo secco % *", "r3_rs", required=True, min_value=0.0001, max_value=100)
            with p3:
                kg_maltodestrina, malto_ok = float_field("Kg maltodestrina *", "r3_malto", required=True, min_value=0)

            mix = calcola_miscele(kg_molle, residuo_secco, kg_maltodestrina)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Kg secco puro", f"{mix['kg_secco_puro']:.2f}")
            m2.metric("Kg polvere teorica", f"{mix['kg_polvere_teorica']:.2f}")
            m3.metric("Taglio maltodestrina", f"{mix['taglio_maltodestrina_pct']:.1f}%")
            m4.metric("Estratto puro", f"{mix['estratto_puro_pct']:.1f}%")

            evento.update({
                "lotto_molle": lotto_molle,
                "codice_prodotto": "" if prodotto is None else prodotto["codice_prodotto"],
                "descrizione_prodotto": "" if prodotto is None else prodotto["descrizione_prodotto"],
                "kg_molle": kg_molle,
                "residuo_secco": residuo_secco,
                "kg_secco_puro": mix["kg_secco_puro"],
                "kg_maltodestrina": kg_maltodestrina,
                "kg_polvere_teorica": mix["kg_polvere_teorica"],
                "taglio_maltodestrina_pct": mix["taglio_maltodestrina_pct"],
                "estratto_puro_pct": mix["estratto_puro_pct"],
            })

        elif tipo_produzione == "Prosecuzione lotto":
            lotti = leggi_lotti()
            lotti_aperti = lotti[lotti["stato_lotto"].astype(str) == "APERTO"]["lotto_molle"].dropna().astype(str).tolist() if not lotti.empty else []
            options = ["-- Inserisci manualmente --"] + lotti_aperti
            scelta, scelta_ok = select_field("Lotto molle aperto", options, "r3_lotto_aperto", required=False)

            if scelta == "-- Inserisci manualmente --" or not scelta:
                lotto_molle, lotto_ok = text_field("Lotto molle *", "r3_lotto_molle", required=True)
            else:
                lotto_molle = scelta
                lotto_ok = True
                field_box_start("Lotto molle selezionato", "green")
                st.markdown(f"<b style='color:#000'>{lotto_molle}</b>", unsafe_allow_html=True)
                field_box_end()

            evento.update({"lotto_molle": lotto_molle})

        elif tipo_produzione == "Chiusura lotto":
            lotti = leggi_lotti()
            lotti_aperti = lotti[lotti["stato_lotto"].astype(str) == "APERTO"]["lotto_molle"].dropna().astype(str).tolist() if not lotti.empty else []
            options = ["-- Inserisci manualmente --"] + lotti_aperti
            scelta, scelta_ok = select_field("Lotto molle da chiudere", options, "r3_lotto_chiusura", required=False)

            if scelta == "-- Inserisci manualmente --" or not scelta:
                lotto_molle, lotto_ok = text_field("Lotto molle *", "r3_lotto_molle", required=True)
            else:
                lotto_molle = scelta
                lotto_ok = True
                field_box_start("Lotto molle selezionato", "green")
                st.markdown(f"<b style='color:#000'>{lotto_molle}</b>", unsafe_allow_html=True)
                field_box_end()

            kg_polvere_finale, kg_fin_ok = float_field("Kg polvere finale *", "r3_kg_finale", required=True, min_value=0.0001)

            lotti_all = prepara_lotti(leggi_lotti())
            rec = lotti_all[lotti_all["lotto_molle"].astype(str) == str(lotto_molle)] if not lotti_all.empty else pd.DataFrame()

            if not rec.empty:
                base = rec.iloc[0]
                estratto_puro_pct = base["estratto_puro_pct"]
                kg_equiv = kg_polvere_finale * safe_div((estratto_puro_pct / 100), STANDARD_ESTRATTO_PURO)

                st.info(
                    f"Composizione recuperata da apertura: estratto puro {estratto_puro_pct:.1f}% | "
                    f"kg equivalenti standard 40% = {kg_equiv:.2f}"
                )

                evento.update({
                    "lotto_molle": lotto_molle,
                    "codice_prodotto": base["codice_prodotto"],
                    "descrizione_prodotto": base["descrizione_prodotto"],
                    "kg_molle": base["kg_molle"],
                    "residuo_secco": base["residuo_secco"],
                    "kg_secco_puro": base["kg_secco_puro"],
                    "kg_maltodestrina": base["kg_maltodestrina"],
                    "kg_polvere_teorica": base["kg_polvere_teorica"],
                    "taglio_maltodestrina_pct": base["taglio_maltodestrina_pct"],
                    "estratto_puro_pct": estratto_puro_pct,
                    "kg_polvere_finale": kg_polvere_finale,
                    "kg_equivalenti_standard": kg_equiv,
                })
            else:
                st.warning("Lotto non trovato tra i lotti aperti. Sarà salvato, ma l'equivalente resterà 0 finché non sarà presente un'apertura lotto.")
                evento.update({"lotto_molle": lotto_molle, "kg_polvere_finale": kg_polvere_finale})

    else:
        note = note_field("Note evento", "r3_note")
        evento["note"] = note

    if evento_mod is None:
        submit_evento = st.button("➕ Aggiungi evento al turno", type="primary")
        submit_modifica = False
        submit_annulla = False
    else:
        b1, b2 = st.columns(2)
        with b1:
            submit_modifica = st.button("💾 Salva modifiche evento", type="primary")
        with b2:
            submit_annulla = st.button("Annulla modifica", type="secondary")
        submit_evento = False

    if submit_evento or submit_modifica:
        mancanti = controlla_campi_obbligatori(tipo_evento, evento)

        if mancanti:
            st.error("Completa i campi obbligatori: " + ", ".join(mancanti))
        elif tipo_evento == "Produzione" and durata_h < (1 / 60):
            st.error("La produzione deve durare almeno 1 minuto.")
        else:
            if submit_modifica and idx_mod is not None:
                st.session_state["eventi_turno_buffer"][idx_mod] = evento
                st.session_state["evento_da_modificare"] = None
            else:
                st.session_state["eventi_turno_buffer"].append(evento)

            st.rerun()

    if submit_annulla:
        st.session_state["evento_da_modificare"] = None
        st.rerun()

    st.divider()
    st.markdown("### Eventi inseriti nel turno")

    eventi_buffer = pd.DataFrame(st.session_state["eventi_turno_buffer"])

    if eventi_buffer.empty:
        st.info("Nessun evento inserito.")
    else:
        st.dataframe(eventi_buffer, use_container_width=True)

        st.markdown("### Gestione evento selezionato")

        indice_evento = st.selectbox(
            "Seleziona evento",
            range(len(eventi_buffer)),
            format_func=lambda x: (
                f"{x + 1} - {eventi_buffer.iloc[x]['tipo_evento']} "
                f"{eventi_buffer.iloc[x].get('tipo_produzione', '')} "
                f"({eventi_buffer.iloc[x]['ora_inizio']} - {eventi_buffer.iloc[x]['ora_fine']})"
            )
        )

        g1, g2, g3 = st.columns(3)
        with g1:
            if st.button("Modifica evento", type="primary"):
                st.session_state["evento_da_modificare"] = indice_evento
                st.rerun()
        with g2:
            if st.button("Elimina evento", type="secondary"):
                st.session_state["eventi_turno_buffer"].pop(indice_evento)
                st.session_state["evento_da_modificare"] = None
                st.rerun()
        with g3:
            if st.button("Duplica evento", type="secondary"):
                nuovo = st.session_state["eventi_turno_buffer"][indice_evento].copy()
                st.session_state["eventi_turno_buffer"].insert(indice_evento + 1, nuovo)
                st.rerun()

        ore_produzione = eventi_buffer[eventi_buffer["tipo_evento"] == "Produzione"]["durata_h"].sum()
        ore_fermo = eventi_buffer[eventi_buffer["tipo_evento"] != "Produzione"]["durata_h"].sum()
        copertura = ore_produzione + ore_fermo

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ore produzione", f"{ore_produzione:.2f}")
        c2.metric("Ore fermo", f"{ore_fermo:.2f}")
        c3.metric("Copertura turno", f"{safe_div(copertura, TURNO_H):.1%}")
        c4.metric("Kg teorici apertura", f"{eventi_buffer['kg_polvere_teorica'].sum():.1f}")

        scostamento = copertura - TURNO_H

        if abs(scostamento) <= 0.01:
            st.markdown("<div class='alert-ok'>Copertura turno corretta: gli eventi coprono le 8 ore pianificate.</div>", unsafe_allow_html=True)
        elif scostamento > 0:
            st.markdown(f"<div class='alert-standby'>Attenzione: gli eventi superano il turno di {scostamento:.2f} h. Il turno resta in stand-by.</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='alert-standby'>Attenzione: mancano {abs(scostamento):.2f} h per coprire le 8 ore. Il turno resta in stand-by.</div>", unsafe_allow_html=True)

        r1, r2 = st.columns(2)
        with r1:
            if st.button("Svuota eventi turno", type="secondary"):
                reset_buffer()
                st.rerun()

        with r2:
            if st.button("🟢 Salva turno", type="primary"):
                if data_turno is None:
                    st.error("Turno non salvato: devi inserire la data turno.")
                    st.stop()

                if turno is None:
                    st.error("Turno non salvato: devi selezionare il turno.")
                    st.stop()

                if abs(copertura - TURNO_H) > 0.01:
                    st.error("Turno non salvato: la somma degli eventi non coincide con le 8 ore pianificate.")
                    st.stop()

                id_turno = nuovo_id()
                eventi_storico = leggi_eventi()

                rows = []
                for i, ev in enumerate(st.session_state["eventi_turno_buffer"], start=1):
                    row = {
                        "id_evento": f"{id_turno}-E{i}",
                        "id_turno": id_turno,
                        "data": str(data_turno),
                        "turno": turno,
                    }
                    row.update(ev)
                    rows.append(row)

                eventi_storico = pd.concat([eventi_storico, pd.DataFrame(rows)], ignore_index=True)
                salva_csv(eventi_storico, EVENTI_FILE, COL_EVENTI)
                aggiorna_lotti_da_eventi()

                reset_buffer()
                st.session_state["salvato"] = True
                st.rerun()

# ============================================================
# LOTTI IN CORSO
# ============================================================

with tab_lotti:
    st.subheader("📦 Lotti in corso e lotti chiusi")

    aggiorna_lotti_da_eventi()
    lotti = prepara_lotti(leggi_lotti())

    if lotti.empty:
        st.info("Nessun lotto registrato.")
    else:
        f1, f2 = st.columns(2)
        with f1:
            stato_filter = st.selectbox("Filtro stato lotto", ["Tutti", "APERTO", "CHIUSO"])
        with f2:
            analisi_filter = st.selectbox("Filtro stato analisi", ["Tutti", "NON_APPLICABILE", "ATTESA_ANALISI", "CONFORME", "NON_CONFORME"])

        lotti_f = lotti.copy()

        if stato_filter != "Tutti":
            lotti_f = lotti_f[lotti_f["stato_lotto"] == stato_filter]

        if analisi_filter != "Tutti":
            lotti_f = lotti_f[lotti_f["stato_analisi"] == analisi_filter]

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Lotti aperti", len(lotti[lotti["stato_lotto"] == "APERTO"]))
        k2.metric("Lotti attesa analisi", len(lotti[lotti["stato_analisi"] == "ATTESA_ANALISI"]))
        k3.metric("Kg fisici chiusi", f"{lotti['kg_polvere_finale'].sum():.1f}")
        k4.metric("Kg equivalenti 40%", f"{lotti['kg_equivalenti_standard'].sum():.1f}")

        st.dataframe(lotti_f, use_container_width=True)

# ============================================================
# QUALITÀ
# ============================================================

with tab_qualita:
    st.subheader("🧪 Rilascio qualità")

    aggiorna_lotti_da_eventi()
    lotti = prepara_lotti(leggi_lotti())

    attesa = lotti[lotti["stato_analisi"] == "ATTESA_ANALISI"].copy() if not lotti.empty else lotti

    if attesa.empty:
        st.info("Nessun lotto in attesa analisi.")
    else:
        attesa["label"] = (
            attesa["lotto_molle"].astype(str) + " | " +
            attesa["codice_prodotto"].astype(str) + " | " +
            attesa["data_chiusura"].dt.strftime("%d/%m/%Y")
        )

        label = st.selectbox("Seleziona lotto", attesa["label"].tolist())
        lotto_sel = attesa[attesa["label"] == label].iloc[0]

        st.write("Prodotto:", lotto_sel["descrizione_prodotto"])
        st.write("Kg polvere finale:", lotto_sel["kg_polvere_finale"])
        st.write("Kg equivalenti standard 40%:", lotto_sel["kg_equivalenti_standard"])

        with st.form("form_qualita"):
            esito = st.radio("Esito", ["CONFORME", "NON_CONFORME"], horizontal=True)

            if esito == "CONFORME":
                kg_conformi = float(lotto_sel["kg_polvere_finale"])
                kg_nc = 0.0
                causa_nc = ""
                note_nc = ""
                st.metric("Kg conformi", f"{kg_conformi:.2f}")
            else:
                kg_conformi = st.number_input("Kg conformi", min_value=0.0, max_value=float(lotto_sel["kg_polvere_finale"]), step=1.0)
                kg_nc = max(float(lotto_sel["kg_polvere_finale"]) - kg_conformi, 0)
                st.metric("Kg NC", f"{kg_nc:.2f}")
                causa_nc = st.selectbox("Causa NC", CAUSE_NC)
                note_nc = st.text_area("Note NC")

            data_rilascio = st.date_input("Data rilascio analisi")
            salva_q = st.form_submit_button("Salva esito analisi", type="primary")

        if salva_q:
            df = leggi_lotti()
            mask = df["lotto_molle"].astype(str) == str(lotto_sel["lotto_molle"])

            for col, val in {
                "stato_analisi": esito,
                "kg_conformi": kg_conformi,
                "kg_nc": kg_nc,
                "causa_nc": causa_nc,
                "note_nc": note_nc,
                "data_rilascio_analisi": str(data_rilascio),
            }.items():
                df[col] = df[col].astype("object")
                df.loc[mask, col] = str(val)

            salva_csv(df, LOTTI_FILE, COL_LOTTI)
            st.session_state["salvato"] = True
            st.rerun()

# ============================================================
# CRUSCOTTO
# ============================================================

with tab_cruscotto:
    st.subheader("📊 Cruscotto OEE")

    aggiorna_lotti_da_eventi()
    eventi = prepara_eventi(leggi_eventi())
    lotti = prepara_lotti(leggi_lotti())

    if eventi.empty:
        st.info("Nessun dato disponibile.")
    else:
        kpi = calcola_kpi(eventi, lotti)

        a, b = st.columns([1.2, 1])

        with a:
            st.plotly_chart(gauge_oee(kpi["oee"]), use_container_width=True)

        with b:
            st.metric("Disponibilità operativa", f"{kpi['availability']:.1%}")
            st.metric("Disponibilità tecnica", f"{kpi['availability_technical']:.1%}")
            st.metric("Performance equivalente", f"{kpi['performance_eq']:.1%}")
            st.metric("Qualità", f"{kpi['quality']:.1%}")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Kg fisici", f"{kpi['kg_fisici']:.1f}")
        m2.metric("Kg equivalenti 40%", f"{kpi['kg_equiv']:.1f}")
        m3.metric("Kg secco puro", f"{kpi['kg_puro']:.1f}")
        m4.metric("Taglio medio", f"{kpi['taglio_medio']:.1f}%")

        st.divider()

        c1, c2 = st.columns(2)

        with c1:
            fermi = eventi[eventi["tipo_evento"] != "Produzione"]
            if fermi.empty:
                st.info("Nessun fermo registrato.")
            else:
                fermi_g = fermi.groupby("tipo_evento", as_index=False)["durata_h"].sum()
                st.plotly_chart(px.bar(fermi_g, x="tipo_evento", y="durata_h", title="Ore fermo per causale"), use_container_width=True)

        with c2:
            if lotti.empty:
                st.info("Nessun lotto.")
            else:
                lotti_g = lotti.groupby("stato_analisi", as_index=False)["lotto_molle"].count()
                st.plotly_chart(px.bar(lotti_g, x="stato_analisi", y="lotto_molle", title="Lotti per stato qualità"), use_container_width=True)

        st.divider()

        excel_data = crea_excel_completo()
        st.download_button(
            label="📥 Scarica Excel completo",
            data=excel_data,
            file_name="oee_spray_dryer_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

# ============================================================
# ASSUNZIONI E FORMULE
# ============================================================

with tab_formule:
    st.subheader("📖 Assunzioni e formule")

    image_path = ASSETS_DIR / "oee_reference.jpeg"
    if image_path.exists():
        st.image(str(image_path), caption="Schema generale OEE - Availability × Performance × Quality", use_container_width=True)

    st.markdown("""
## 1. Formula generale OEE

`OEE = Disponibilità × Performance × Qualità`

---

## 2. Disponibilità

`Disponibilità operativa = (Tempo pianificato - Tutti i fermi) / Tempo pianificato`

Il tempo pianificato è pari a **8 ore per turno**.

Sono considerati fermi operativi:
- Attesa prodotto
- Attesa analisi
- Cambio lotto
- Lavaggio
- Guasto
- Manutenzione programmata
- Manutenzione straordinaria
- Pulizia
- Altro

La **Disponibilità tecnica** considera solo:
- Guasto
- Manutenzione straordinaria

---

## 3. Performance equivalente

La produzione fisica non è sempre confrontabile perché i prodotti possono avere percentuali diverse di maltodestrina.

Per questo motivo la dashboard calcola una performance basata sui **kg equivalenti standard al 40% di estratto puro**.

### Standard aziendale

Prodotto standard:

- **40% estratto puro**
- **60% maltodestrina**

### Esempio di equivalenza

Prodotto standard 60/40:

- 100 kg di prodotto standard contengono 40 kg di estratto puro.

Prodotto reale 70/30:

- 100 kg di prodotto reale contengono 30 kg di estratto puro e 70 kg di maltodestrina.

Ci chiediamo:

**A quanti kg di prodotto standard al 40% corrispondono quei 30 kg di puro?**

Nel prodotto standard:

`0,40 × X = 30`

quindi:

`X = 30 / 0,40 = 75`

Conclusione:

**100 kg di prodotto al 70/30 equivalgono a 75 kg di prodotto standard al 60/40**, perché contengono la stessa quantità di estratto puro.

---

## 4. Calcoli lotto

L'operatore inserisce in apertura lotto:

- kg molle
- residuo secco %
- kg maltodestrina aggiunta

La dashboard calcola:

### Kg secco puro

`kg secco puro = kg molle × residuo secco % / 100`

### Kg polvere teorica

`kg polvere teorica = kg secco puro + kg maltodestrina`

### Taglio maltodestrina

`taglio % = kg maltodestrina / kg polvere teorica × 100`

### Estratto puro %

`estratto puro % = kg secco puro / kg polvere teorica × 100`

### Kg equivalenti standard

Alla chiusura del lotto, dopo aver inserito i kg di polvere finale:

`kg equivalenti standard = kg polvere finale × (estratto puro % / 40%)`

---

## 5. Qualità

La qualità viene calcolata solo sui lotti rilasciati dal laboratorio.

`Qualità = kg conformi / kg prodotti analizzati`

---

## 6. OEE finale

`OEE = Disponibilità operativa × Performance equivalente × Qualità`
""")

# ============================================================
# ANAGRAFICA PRODOTTI
# ============================================================

with tab_prodotti:
    st.subheader("📚 Anagrafica prodotti")

    prodotti = leggi_prodotti()

    if len(prodotti) == 1 and str(prodotti.iloc[0]["codice_prodotto"]) == "INSERIRE":
        st.warning("Anagrafica prodotti non caricata. Carica il file data/prodotti.csv incluso nel pacchetto.")

    st.dataframe(prodotti, use_container_width=True)

    with st.form("form_prodotto"):
        codice = st.text_input("Codice prodotto")
        descrizione = st.text_input("Descrizione prodotto")
        capacita = st.number_input("Capacità nominale equivalente kg/h", min_value=0.0, value=20.0, step=1.0)
        salva_p = st.form_submit_button("Salva prodotto", type="primary")

    if salva_p:
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

    st.divider()

    st.download_button(
        label="📥 Scarica anagrafica prodotti Excel",
        data=crea_excel_completo(),
        file_name="oee_spray_dryer_anagrafica_e_dati.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="secondary",
    )

# ============================================================
# GESTIONE DATI
# ============================================================

with tab_gestione:
    st.subheader("🔒 Gestione dati riservata")

    password = st.text_input("Password gestione", type="password")

    if password != ADMIN_PASSWORD:
        st.info("Inserisci la password per modificare o cancellare dati già salvati.")
        st.stop()

    st.success("Accesso gestione abilitato.")

    eventi = leggi_eventi()
    lotti = leggi_lotti()

    st.markdown("## Eventi turno")
    st.dataframe(eventi, use_container_width=True)

    if not eventi.empty:
        id_evento = st.selectbox("Evento da eliminare", eventi["id_evento"].astype(str).tolist())
        if st.button("Elimina evento selezionato", type="secondary"):
            eventi = eventi[eventi["id_evento"].astype(str) != str(id_evento)]
            salva_csv(eventi, EVENTI_FILE, COL_EVENTI)
            aggiorna_lotti_da_eventi()
            st.session_state["salvato"] = True
            st.rerun()

    st.markdown("## Lotti")
    st.dataframe(lotti, use_container_width=True)

    if not lotti.empty:
        lotto_del = st.selectbox("Lotto da eliminare", lotti["lotto_molle"].astype(str).tolist())
        if st.button("Elimina lotto e relativi eventi", type="secondary"):
            lotti = lotti[lotti["lotto_molle"].astype(str) != str(lotto_del)]
            eventi = eventi[eventi["lotto_molle"].astype(str) != str(lotto_del)]
            salva_csv(lotti, LOTTI_FILE, COL_LOTTI)
            salva_csv(eventi, EVENTI_FILE, COL_EVENTI)
            st.session_state["salvato"] = True
            st.rerun()

    st.divider()

    st.markdown("## Export e ripristino dati")

    excel_data = crea_excel_completo()
    st.download_button(
        label="📥 Scarica Excel completo",
        data=excel_data,
        file_name="oee_spray_dryer_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )

    eventi_xlsx = BytesIO()
    with pd.ExcelWriter(eventi_xlsx, engine="openpyxl") as writer:
        leggi_eventi().to_excel(writer, sheet_name="Eventi turno", index=False)
    eventi_xlsx.seek(0)

    st.download_button(
        label="📥 Scarica solo eventi Excel",
        data=eventi_xlsx,
        file_name="oee_spray_dryer_eventi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="secondary",
    )

    uploaded = st.file_uploader(
        "Carica Excel di backup per ripristino",
        type=["xlsx"],
        help="Puoi caricare l'export completo generato dalla dashboard. Il ripristino è protetto da password."
    )

    if uploaded is not None:
        try:
            imported = importa_excel(uploaded)

            st.info(
                "File letto correttamente. Contenuto trovato: "
                + ", ".join(imported.keys())
            )

            conferma_import = st.checkbox(
                "Confermo di voler sostituire i dati attuali con quelli del file caricato"
            )

            if st.button("Ripristina dati da Excel", type="primary"):
                if not conferma_import:
                    st.error("Per procedere devi confermare la sostituzione dei dati.")
                    st.stop()

                if "eventi" in imported:
                    salva_csv(imported["eventi"], EVENTI_FILE, COL_EVENTI)

                if "lotti" in imported:
                    salva_csv(imported["lotti"], LOTTI_FILE, COL_LOTTI)

                if "prodotti" in imported:
                    salva_csv(imported["prodotti"], PRODOTTI_FILE, COL_PRODOTTI)

                aggiorna_lotti_da_eventi()
                st.session_state["salvato"] = True
                st.rerun()

        except Exception as e:
            st.error(f"Errore durante la lettura del file Excel: {e}")

    st.divider()

    if st.button("Cancella tutto lo storico eventi", type="secondary"):
        pd.DataFrame(columns=COL_EVENTI).to_csv(EVENTI_FILE, index=False)
        pd.DataFrame(columns=COL_LOTTI).to_csv(LOTTI_FILE, index=False)
        st.session_state["salvato"] = True
        st.rerun()
