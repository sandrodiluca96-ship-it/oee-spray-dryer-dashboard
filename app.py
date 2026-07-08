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
/* Pulsanti principali */
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background-color: #2E7D32 !important;
    color: white !important;
    border: 1px solid #2E7D32 !important;
    font-weight: 700 !important;
}

/* Pulsanti secondari */
.stButton > button[kind="secondary"],
.stFormSubmitButton > button[kind="secondary"] {
    border: 1px solid #757575 !important;
    font-weight: 600 !important;
}

/* Alert operativo */
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
CAUSALI_FILE = DATA_DIR / "causali_evento.csv"
FERMI_PROGRAMMATI_FILE = DATA_DIR / "fermi_programmati.csv"
STORICO_MENSILE_FILE = DATA_DIR / "storico_mensile.csv"

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

COL_CAUSALI = ["causale","categoria","escludi_da_tempo_pianificato","perdita_disponibilita","attiva"]
COL_FERMI_PROGRAMMATI = ["id_fermo_programmato","data","ora_inizio","ora_fine","durata_h","causale","note"]
COL_STORICO_MENSILE = ["mese", "kg_fisici", "kg_equivalenti_40", "giorni_produttivi", "note"]

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
    if not CAUSALI_FILE.exists():
        pd.DataFrame([
            {"causale":"Attesa prodotto","categoria":"Fermo non programmato","escludi_da_tempo_pianificato":"NO","perdita_disponibilita":"SI","attiva":"SI"},
            {"causale":"Attesa analisi","categoria":"Fermo non programmato","escludi_da_tempo_pianificato":"NO","perdita_disponibilita":"SI","attiva":"SI"},
            {"causale":"Cambio lotto","categoria":"Fermo programmato","escludi_da_tempo_pianificato":"SI","perdita_disponibilita":"NO","attiva":"SI"},
            {"causale":"Lavaggio","categoria":"Fermo programmato","escludi_da_tempo_pianificato":"SI","perdita_disponibilita":"NO","attiva":"SI"},
            {"causale":"Guasto","categoria":"Fermo non programmato","escludi_da_tempo_pianificato":"NO","perdita_disponibilita":"SI","attiva":"SI"},
            {"causale":"Manutenzione programmata","categoria":"Fermo programmato","escludi_da_tempo_pianificato":"SI","perdita_disponibilita":"NO","attiva":"SI"},
            {"causale":"Manutenzione straordinaria","categoria":"Fermo non programmato","escludi_da_tempo_pianificato":"NO","perdita_disponibilita":"SI","attiva":"SI"},
            {"causale":"Pulizia","categoria":"Fermo programmato","escludi_da_tempo_pianificato":"SI","perdita_disponibilita":"NO","attiva":"SI"},
            {"causale":"Altro","categoria":"Fermo non programmato","escludi_da_tempo_pianificato":"NO","perdita_disponibilita":"SI","attiva":"SI"},
        ]).to_csv(CAUSALI_FILE, index=False)
    if not FERMI_PROGRAMMATI_FILE.exists():
        pd.DataFrame(columns=COL_FERMI_PROGRAMMATI).to_csv(FERMI_PROGRAMMATI_FILE, index=False)

    if not STORICO_MENSILE_FILE.exists():
        pd.DataFrame(columns=COL_STORICO_MENSILE).to_csv(STORICO_MENSILE_FILE, index=False)


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

def leggi_causali():
    return leggi_csv(CAUSALI_FILE, COL_CAUSALI)

def causali_attive():
    df = leggi_causali()
    if df.empty:
        return [x for x in TIPI_EVENTO if x != "Produzione"]
    return df[df["attiva"].astype(str).str.upper()=="SI"]["causale"].astype(str).tolist()

def leggi_fermi_programmati():
    return leggi_csv(FERMI_PROGRAMMATI_FILE, COL_FERMI_PROGRAMMATI)

def leggi_storico_mensile():
    df = leggi_csv(STORICO_MENSILE_FILE, COL_STORICO_MENSILE)
    if not df.empty:
        df["kg_fisici"] = pd.to_numeric(df["kg_fisici"], errors="coerce").fillna(0)
        df["kg_equivalenti_40"] = pd.to_numeric(df["kg_equivalenti_40"], errors="coerce").fillna(0)
        df["giorni_produttivi"] = pd.to_numeric(df["giorni_produttivi"], errors="coerce").fillna(0)
    return df

def salva_storico_mensile(df):
    salva_csv(df, STORICO_MENSILE_FILE, COL_STORICO_MENSILE)

def prepara_fermi_programmati(df):
    if df.empty:
        return df
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["durata_h"] = pd.to_numeric(df["durata_h"], errors="coerce").fillna(0)
    return df


def visualizza_prodotti(df):
    return df.rename(columns={
        "codice_prodotto": "Codice prodotto",
        "descrizione_prodotto": "Descrizione prodotto",
        "capacita_kg_h": "Capacità nominale equivalente kg/h",
    })


def visualizza_causali(df):
    return df.rename(columns={
        "causale": "Causale",
        "categoria": "Categoria",
        "escludi_da_tempo_pianificato": "Escludi dal tempo pianificato",
        "perdita_disponibilita": "Perdita di disponibilità",
        "attiva": "Attiva",
    })


def visualizza_fermi_programmati(df):
    return df.rename(columns={
        "id_fermo_programmato": "ID fermo programmato",
        "data": "Data",
        "ora_inizio": "Ora inizio",
        "ora_fine": "Ora fine",
        "durata_h": "Durata h",
        "causale": "Causale",
        "note": "Note",
    })


def visualizza_eventi(df):
    return df.rename(columns={
        "id_evento": "ID evento",
        "id_turno": "ID turno",
        "data": "Data",
        "turno": "Turno",
        "tipo_evento": "Tipo evento",
        "tipo_produzione": "Tipo produzione",
        "lotto_molle": "Lotto molle",
        "codice_prodotto": "Codice prodotto",
        "descrizione_prodotto": "Descrizione prodotto",
        "ora_inizio": "Ora inizio",
        "ora_fine": "Ora fine",
        "durata_h": "Durata h",
        "kg_molle": "Kg molle",
        "residuo_secco": "Residuo secco %",
        "kg_secco_puro": "Kg secco puro",
        "kg_maltodestrina": "Kg maltodestrina",
        "kg_polvere_teorica": "Kg polvere teorica",
        "taglio_maltodestrina_pct": "Taglio maltodestrina %",
        "estratto_puro_pct": "Estratto puro %",
        "kg_polvere_finale": "Kg polvere finale",
        "kg_equivalenti_standard": "Kg equivalenti standard",
        "note": "Note",
    })


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

        txt = str(value).strip()

        if "/" in txt:
            return datetime.strptime(txt, "%d/%m/%Y").date()

        return datetime.strptime(txt, "%Y-%m-%d").date()

    except Exception:
        return None


def lista_orari_15min():
    return [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 15, 30, 45)]


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


def lista_lotti_aperti():
    """Restituisce i lotti aperti da storico + aperture presenti nel turno corrente non ancora salvato."""
    valori = []

    # Aggiorna sempre l'archivio lotti prima di costruire l'elenco.
    # Serve quando un'apertura lotto è stata salvata negli eventi ma lotti.csv non è ancora allineato.
    try:
        aggiorna_lotti_da_eventi()
    except Exception:
        pass

    lotti = leggi_lotti()
    if not lotti.empty:
        valori += lotti[lotti["stato_lotto"].astype(str) == "APERTO"]["lotto_molle"].dropna().astype(str).tolist()

    # Ricostruzione di sicurezza dagli eventi salvati:
    eventi_salvati = leggi_eventi()
    if not eventi_salvati.empty:
        aperture_salvate = eventi_salvati[
            (eventi_salvati["tipo_evento"].astype(str) == "Produzione")
            & (eventi_salvati["tipo_produzione"].astype(str) == "Apertura lotto")
        ]["lotto_molle"].dropna().astype(str).tolist()

        chiusure_salvate = eventi_salvati[
            (eventi_salvati["tipo_evento"].astype(str) == "Produzione")
            & (eventi_salvati["tipo_produzione"].astype(str) == "Chiusura lotto")
        ]["lotto_molle"].dropna().astype(str).tolist()

        valori += [x for x in aperture_salvate if x not in chiusure_salvate]

    buffer = pd.DataFrame(st.session_state.get("eventi_turno_buffer", []))
    if not buffer.empty and "lotto_molle" in buffer.columns:
        aperture_buffer = buffer[
            (buffer["tipo_evento"] == "Produzione")
            & (buffer["tipo_produzione"] == "Apertura lotto")
        ]
        valori += aperture_buffer["lotto_molle"].dropna().astype(str).tolist()

    # Rimuove vuoti e duplicati mantenendo l'ordine
    out = []
    for v in valori:
        v = str(v).strip()
        if v and v not in out:
            out.append(v)

    return out


def lotto_aperto_corrente():
    """Restituisce il lotto aperto da proporre automaticamente nei nuovi eventi di produzione.

    Regola operativa: se esiste almeno un lotto aperto, l'app lo considera lotto corrente
    e lo preseleziona per Prosecuzione lotto e Chiusura lotto. In caso di più lotti aperti,
    viene proposto l'ultimo lotto presente nell'elenco ricostruito; l'operatore può comunque
    selezionarne un altro.
    """
    lotti_aperti = lista_lotti_aperti()
    if not lotti_aperti:
        return ""
    return lotti_aperti[-1]


def recupera_lotto_molle(lotto_molle):
    """Recupera prodotto e composizione partendo dal lotto molle."""
    lotto_molle = str(lotto_molle).strip()

    if lotto_molle == "":
        return None

    lotti = prepara_lotti(leggi_lotti())
    if not lotti.empty:
        match = lotti[lotti["lotto_molle"].astype(str) == lotto_molle]
        if not match.empty:
            return match.iloc[0].to_dict()

    eventi = prepara_eventi(leggi_eventi())
    if not eventi.empty:
        match = eventi[
            (eventi["lotto_molle"].astype(str) == lotto_molle)
            & (eventi["tipo_evento"] == "Produzione")
            & (eventi["tipo_produzione"] == "Apertura lotto")
        ]
        if not match.empty:
            return match.iloc[0].to_dict()

    buffer = pd.DataFrame(st.session_state.get("eventi_turno_buffer", []))
    if not buffer.empty and "lotto_molle" in buffer.columns:
        match = buffer[
            (buffer["lotto_molle"].astype(str) == lotto_molle)
            & (buffer["tipo_evento"] == "Produzione")
            & (buffer["tipo_produzione"] == "Apertura lotto")
        ]
        if not match.empty:
            return match.iloc[0].to_dict()

    return None


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
        leggi_causali().to_excel(writer, sheet_name="Causali", index=False)
        leggi_fermi_programmati().to_excel(writer, sheet_name="Fermi programmati", index=False)

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
    if "Causali" in xls.sheet_names:
        imported["causali"] = pd.read_excel(xls, sheet_name="Causali", dtype=str).fillna("")
    if "Fermi programmati" in xls.sheet_names:
        imported["fermi_programmati"] = pd.read_excel(xls, sheet_name="Fermi programmati", dtype=str).fillna("")
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
    tempo_lordo = turni * TURNO_H

    fermi = eventi[eventi["tipo_evento"] != "Produzione"].copy()
    cfg = leggi_causali()
    escluse = cfg[cfg["escludi_da_tempo_pianificato"].astype(str).str.upper()=="SI"]["causale"].astype(str).tolist() if not cfg.empty else []
    perdite = cfg[cfg["perdita_disponibilita"].astype(str).str.upper()=="SI"]["causale"].astype(str).tolist() if not cfg.empty else []

    ore_escluse = fermi[fermi["tipo_evento"].isin(escluse)]["durata_h"].sum() if not fermi.empty else 0
    ore_perdita = fermi[fermi["tipo_evento"].isin(perdite)]["durata_h"].sum() if not fermi.empty else 0

    fp = prepara_fermi_programmati(leggi_fermi_programmati())
    if not fp.empty and not eventi.empty:
        date_eventi = pd.to_datetime(eventi["data"], errors="coerce").dropna()
        if not date_eventi.empty:
            fp = fp[(fp["data"] >= date_eventi.min()) & (fp["data"] <= date_eventi.max())]
            ore_escluse += fp["durata_h"].sum()

    tempo_netto = max(tempo_lordo - ore_escluse, 0)
    availability = max(0, safe_div(tempo_netto - ore_perdita, tempo_netto))
    ore_fermo_tecnico = fermi[fermi["tipo_evento"].isin(CAUSALI_TECNICHE)]["durata_h"].sum() if not fermi.empty else 0
    availability_technical = max(0, safe_div(tempo_lordo - ore_fermo_tecnico, tempo_lordo))

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



def prepara_lotti_per_production_report(lotti):
    """Prepara lotti chiusi per la pagina Production vs Target."""
    lotti = prepara_lotti(lotti.copy())
    if lotti.empty:
        return lotti
    out = lotti[lotti["stato_lotto"] == "CHIUSO"].copy()
    if out.empty:
        return out
    out["data_report"] = out["data_chiusura"]
    out.loc[out["data_report"].isna(), "data_report"] = out.loc[out["data_report"].isna(), "data_apertura"]
    out = out.dropna(subset=["data_report"])
    return out


def somma_periodo(lotti, inizio=None, fine=None):
    if lotti.empty:
        return {"kg_fisici": 0.0, "kg_equivalenti_40": 0.0, "lotti": 0}
    df = lotti.copy()
    if inizio is not None:
        df = df[df["data_report"].dt.date >= inizio]
    if fine is not None:
        df = df[df["data_report"].dt.date <= fine]
    return {
        "kg_fisici": float(df["kg_polvere_finale"].sum()) if not df.empty else 0.0,
        "kg_equivalenti_40": float(df["kg_equivalenti_standard"].sum()) if not df.empty else 0.0,
        "lotti": int(len(df)),
    }


def format_delta(actual, target):
    if target <= 0:
        return "n.d."
    delta = actual - target
    pct = safe_div(delta, target) * 100
    return f"{delta:,.1f} ({pct:+.1f}%)".replace(",", "X").replace(".", ",").replace("X", ".")


def media_storica_mensile(colonna):
    storico = leggi_storico_mensile()
    if storico.empty or colonna not in storico.columns:
        return 0.0
    valori = pd.to_numeric(storico[colonna], errors="coerce")
    valori = valori[valori > 0]
    return float(valori.mean()) if not valori.empty else 0.0

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

if "header_reset_counter" not in st.session_state:
    st.session_state["header_reset_counter"] = 0


def reset_buffer(reset_header=False):
    st.session_state["eventi_turno_buffer"] = []
    st.session_state["evento_da_modificare"] = None

    if reset_header:
        st.session_state["header_reset_counter"] = st.session_state.get("header_reset_counter", 0) + 1

        for key in list(st.session_state.keys()):
            if (
                key.startswith("header_data_turno")
                or key.startswith("header_turno")
                or key.startswith("tipo_evento_select")
                or key.startswith("ora_inizio_evento")
                or key.startswith("ora_fine_evento")
                or key.startswith("r3_")
                or key.startswith("lotto_aperto_prosecuzione")
                or key.startswith("lotto_aperto_chiusura")
            ):
                del st.session_state[key]

# ============================================================
# APP
# ============================================================

st.title("⚙️ Dashboard OEE Spray Dryer")
st.caption("Usa il menu laterale per navigare tra le sezioni. La pagina corrente resta isolata dalle altre schermate operative.")

if st.session_state["salvato"]:
    st.session_state["salvato"] = False
    st.success("Turno salvato correttamente. Data, turno ed eventi sono stati azzerati: puoi iniziare un nuovo turno.")

SEZIONI_APP = [
    "Turno",
    "Lotti in corso",
    "Qualità",
    "Production vs Target",
    "Cruscotto OEE",
    "Assunzioni e formule",
    "Anagrafica prodotti",
    "Configurazione",
    "Gestione dati",
]

sezione_corrente = st.sidebar.radio(
    "Sezione",
    SEZIONI_APP,
    index=0,
    key="sezione_corrente",
)

# ============================================================
# TURNO
# ============================================================

if sezione_corrente == "Turno":
    st.subheader("Compilazione turno tramite eventi")

    header_key_suffix = st.session_state.get("header_reset_counter", 0)

    c0, c1 = st.columns(2)
    with c0:
        data_turno = st.date_input("Data turno", value=None, format="DD/MM/YYYY", key=f"header_data_turno_{header_key_suffix}")
    with c1:
        turno_sel = st.selectbox("Turno", ["-- Seleziona turno --", "1", "2", "3"], index=0, key=f"header_turno_{header_key_suffix}")
        turno = None if turno_sel == "-- Seleziona turno --" else turno_sel

    if turno is not None:
        st.caption(
            f"Turno {turno}: {TURNI[turno]['inizio'].strftime('%H:%M')} - "
            f"{TURNI[turno]['fine'].strftime('%H:%M')} | Durata pianificata: 8 h"
        )
    else:
        st.caption("Seleziona il turno per impostare gli orari di riferimento.")

    st.divider()
    st.markdown("### Aggiungi evento")

    prodotti = leggi_prodotti()
    prodotti["label"] = prodotti["codice_prodotto"].astype(str) + " - " + prodotti["descrizione_prodotto"].astype(str)

    idx_mod = st.session_state["evento_da_modificare"]
    evento_mod = None

    if idx_mod is not None and 0 <= idx_mod < len(st.session_state["eventi_turno_buffer"]):
        evento_mod = st.session_state["eventi_turno_buffer"][idx_mod]
        st.info(f"Modifica attiva: evento {idx_mod + 1} - {evento_mod['tipo_evento']}")

    default_tipo = evento_mod["tipo_evento"] if evento_mod else "Produzione"
    default_tipo_index = TIPI_EVENTO.index(default_tipo) if default_tipo in TIPI_EVENTO else 0

    tipi_evento_disponibili = ["Produzione"] + causali_attive()
    default_tipo_index = tipi_evento_disponibili.index(default_tipo) if default_tipo in tipi_evento_disponibili else None
    tipo_evento = st.selectbox("Tipo evento", tipi_evento_disponibili, index=None if evento_mod is None else default_tipo_index, placeholder="Seleziona tipo evento", key="tipo_evento_select")

    if tipo_evento is None:
        st.info("Seleziona il tipo evento per iniziare la compilazione.")
    elif tipo_evento != "Produzione":
        st.caption("Evento di fermo: non sono richiesti prodotto, lotto o quantità.")

    with st.container():
        orari = lista_orari_15min()
        default_start_txt = str(evento_mod["ora_inizio"])[:5] if evento_mod else None
        default_end_txt = str(evento_mod["ora_fine"])[:5] if evento_mod else None

        start_options = ["-- Seleziona ora inizio --"] + orari
        end_options = ["-- Seleziona ora fine --"] + orari

        start_index = start_options.index(default_start_txt) if default_start_txt in start_options else 0
        end_index = end_options.index(default_end_txt) if default_end_txt in end_options else 0

        c2, c3 = st.columns(2)
        with c2:
            ora_inizio_sel = st.selectbox("Ora inizio evento", start_options, index=start_index)
        with c3:
            ora_fine_sel = st.selectbox("Ora fine evento", end_options, index=end_index)

        ora_inizio = None if ora_inizio_sel.startswith("--") else parse_time_manual(ora_inizio_sel)
        ora_fine = None if ora_fine_sel.startswith("--") else parse_time_manual(ora_fine_sel)
        durata_h = ore_da_orari(ora_inizio, ora_fine) if ora_inizio and ora_fine else 0

        if durata_h <= 0:
            st.warning("Selezionare ora inizio e ora fine evento valide.")
        else:
            st.metric("Durata evento", f"{durata_h:.2f} h")

        evento = {
            "tipo_evento": tipo_evento,
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
            lotti_aperti = lista_lotti_aperti()
            lotto_corrente = lotto_aperto_corrente()

            # Se esiste già un lotto aperto, il flusso più probabile al turno successivo
            # è la prosecuzione dello stesso lotto. L'apertura resta comunque selezionabile.
            if evento_mod:
                default_tipo_prod = evento_mod["tipo_produzione"]
            elif lotto_corrente:
                default_tipo_prod = "Prosecuzione lotto"
            else:
                default_tipo_prod = "Apertura lotto"

            default_tipo_prod_idx = TIPI_PRODUZIONE.index(default_tipo_prod) if default_tipo_prod in TIPI_PRODUZIONE else 0

            tipo_produzione = st.selectbox(
                "Tipo produzione",
                TIPI_PRODUZIONE,
                index=default_tipo_prod_idx,
                help="Apertura: inserisci dati di composizione. Prosecuzione: lotto aperto proposto automaticamente. Chiusura: lotto aperto proposto automaticamente e kg polvere finale."
            )

            evento["tipo_produzione"] = tipo_produzione

            if lotto_corrente and tipo_produzione in ["Prosecuzione lotto", "Chiusura lotto"]:
                st.success(f"Lotto aperto rilevato automaticamente: {lotto_corrente}")

            if tipo_produzione == "Apertura lotto":
                lotto_molle = st.text_input("Lotto molle", value=evento_mod["lotto_molle"] if evento_mod else "")

                labels = prodotti["label"].tolist()
                default_prod_idx = 0
                if evento_mod and evento_mod["codice_prodotto"]:
                    matches = prodotti.index[prodotti["codice_prodotto"].astype(str) == str(evento_mod["codice_prodotto"])].tolist()
                    if matches:
                        default_prod_idx = prodotti.index.get_loc(matches[0])

                if evento_mod:
                    prodotto_label = st.selectbox(
                        "Prodotto",
                        labels,
                        index=default_prod_idx,
                        help="Scrivi parte del codice o della descrizione per cercare il semilavorato."
                    )
                else:
                    prodotto_label = st.selectbox(
                        "Prodotto",
                        ["-- Seleziona prodotto --"] + labels,
                        index=0,
                        help="Scrivi parte del codice o della descrizione per cercare il semilavorato."
                    )

                prodotto = None if prodotto_label == "-- Seleziona prodotto --" else prodotti[prodotti["label"] == prodotto_label].iloc[0]

                p1, p2, p3 = st.columns(3)
                with p1:
                    kg_molle_txt = st.text_input("Kg molle", value=str(evento_mod["kg_molle"]) if evento_mod else "", placeholder="es. 1000")
                    kg_molle = safe_float(str(kg_molle_txt).replace(",", "."), 0)
                with p2:
                    residuo_secco_txt = st.text_input("Residuo secco %", value=str(evento_mod["residuo_secco"]) if evento_mod else "", placeholder="es. 30")
                    residuo_secco = safe_float(str(residuo_secco_txt).replace(",", "."), 0)
                with p3:
                    kg_maltodestrina_txt = st.text_input("Kg maltodestrina aggiunta", value=str(evento_mod["kg_maltodestrina"]) if evento_mod else "", placeholder="es. 450")
                    kg_maltodestrina = safe_float(str(kg_maltodestrina_txt).replace(",", "."), 0)

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
                lotti_aperti = lista_lotti_aperti()
                lotto_corrente = lotto_aperto_corrente()
                options = ["-- Seleziona lotto aperto --"] + lotti_aperti
                default_lotto_idx = options.index(lotto_corrente) if lotto_corrente in options else 0
                if evento_mod and str(evento_mod.get("lotto_molle", "")) in options:
                    default_lotto_idx = options.index(str(evento_mod.get("lotto_molle", "")))
                scelta = st.selectbox("Lotto aperto", options, index=default_lotto_idx, key="lotto_aperto_prosecuzione")

                if scelta == "-- Seleziona lotto aperto --":
                    lotto_molle = ""
                    if not lotti_aperti:
                        st.warning(
                            "Non ci sono lotti aperti selezionabili. "
                            "Per fare una prosecuzione devi prima inserire un evento di Apertura lotto."
                        )
                else:
                    lotto_molle = scelta

                st.caption("Prosecuzione lotto: scegli solo il lotto aperto. Prodotto e composizione vengono recuperati automaticamente.")

                dati_lotto = recupera_lotto_molle(lotto_molle)

                if dati_lotto is not None:
                    st.info(
                        f"Prodotto recuperato: {dati_lotto.get('codice_prodotto', '')} - "
                        f"{dati_lotto.get('descrizione_prodotto', '')}"
                    )

                    evento.update({
                        "lotto_molle": lotto_molle,
                        "codice_prodotto": dati_lotto.get("codice_prodotto", ""),
                        "descrizione_prodotto": dati_lotto.get("descrizione_prodotto", ""),
                        "kg_molle": safe_float(dati_lotto.get("kg_molle", 0)),
                        "residuo_secco": safe_float(dati_lotto.get("residuo_secco", 0)),
                        "kg_secco_puro": safe_float(dati_lotto.get("kg_secco_puro", 0)),
                        "kg_maltodestrina": safe_float(dati_lotto.get("kg_maltodestrina", 0)),
                        "kg_polvere_teorica": safe_float(dati_lotto.get("kg_polvere_teorica", 0)),
                        "taglio_maltodestrina_pct": safe_float(dati_lotto.get("taglio_maltodestrina_pct", 0)),
                        "estratto_puro_pct": safe_float(dati_lotto.get("estratto_puro_pct", 0)),
                    })
                else:
                    st.warning("Lotto non trovato. Inserisci prima un evento di Apertura lotto con lo stesso lotto molle.")
                    evento.update({"lotto_molle": lotto_molle})

            elif tipo_produzione == "Chiusura lotto":
                lotti_aperti = lista_lotti_aperti()
                lotto_corrente = lotto_aperto_corrente()
                options = ["-- Seleziona lotto aperto --"] + lotti_aperti
                default_lotto_idx = options.index(lotto_corrente) if lotto_corrente in options else 0
                if evento_mod and str(evento_mod.get("lotto_molle", "")) in options:
                    default_lotto_idx = options.index(str(evento_mod.get("lotto_molle", "")))
                scelta = st.selectbox("Lotto aperto", options, index=default_lotto_idx, key="lotto_aperto_chiusura")

                if scelta == "-- Seleziona lotto aperto --":
                    lotto_molle = ""
                    if not lotti_aperti:
                        st.warning(
                            "Non ci sono lotti aperti selezionabili. "
                            "Per fare una chiusura devi prima inserire un evento di Apertura lotto."
                        )
                else:
                    lotto_molle = scelta

                kg_polvere_finale_txt = st.text_input("Kg polvere finale ottenuta", value=str(evento_mod["kg_polvere_finale"]) if evento_mod else "", placeholder="es. 730")
                kg_polvere_finale = safe_float(str(kg_polvere_finale_txt).replace(",", "."), 0)

                # Recupera prodotto e composizione dal lotto molle, senza reinserire il prodotto
                dati_lotto = recupera_lotto_molle(lotto_molle)

                if dati_lotto is not None:
                    estratto_puro_pct = safe_float(dati_lotto.get("estratto_puro_pct", 0))
                    kg_equiv = kg_polvere_finale * safe_div((estratto_puro_pct / 100), STANDARD_ESTRATTO_PURO)

                    st.info(
                        f"Prodotto recuperato: {dati_lotto.get('codice_prodotto', '')} - "
                        f"{dati_lotto.get('descrizione_prodotto', '')} | "
                        f"estratto puro {estratto_puro_pct:.1f}% | "
                        f"kg equivalenti standard 40% = {kg_equiv:.2f}"
                    )

                    evento.update({
                        "lotto_molle": lotto_molle,
                        "codice_prodotto": dati_lotto.get("codice_prodotto", ""),
                        "descrizione_prodotto": dati_lotto.get("descrizione_prodotto", ""),
                        "kg_molle": safe_float(dati_lotto.get("kg_molle", 0)),
                        "residuo_secco": safe_float(dati_lotto.get("residuo_secco", 0)),
                        "kg_secco_puro": safe_float(dati_lotto.get("kg_secco_puro", 0)),
                        "kg_maltodestrina": safe_float(dati_lotto.get("kg_maltodestrina", 0)),
                        "kg_polvere_teorica": safe_float(dati_lotto.get("kg_polvere_teorica", 0)),
                        "taglio_maltodestrina_pct": safe_float(dati_lotto.get("taglio_maltodestrina_pct", 0)),
                        "estratto_puro_pct": estratto_puro_pct,
                        "kg_polvere_finale": kg_polvere_finale,
                        "kg_equivalenti_standard": kg_equiv,
                    })
                else:
                    st.warning("Lotto non trovato. Inserisci prima un evento di Apertura lotto con lo stesso lotto molle.")
                    evento.update({
                        "lotto_molle": lotto_molle,
                        "kg_polvere_finale": kg_polvere_finale,
                    })

        else:
            note = st.text_area("Note evento", value=evento_mod["note"] if evento_mod else "")
            evento["note"] = note

        if evento_mod is None:
            submit_evento = st.button("Aggiungi evento al turno", type="primary", key="btn_aggiungi_evento")
            submit_modifica = False
            submit_annulla = False
        else:
            b1, b2 = st.columns(2)
            with b1:
                submit_modifica = st.button("Salva modifiche evento", type="primary", key="btn_salva_modifiche_evento")
            with b2:
                submit_annulla = st.button("Annulla modifica", type="secondary", key="btn_annulla_modifica_evento")
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

            for key in ["lotto_aperto_prosecuzione", "lotto_aperto_chiusura"]:
                if key in st.session_state:
                    del st.session_state[key]

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
                reset_buffer(reset_header=False)
                st.rerun()

        with r2:
            if st.button("Salva turno", type="primary"):
                if data_turno is None:
                    st.error("Turno non salvato: devi selezionare la data turno dal calendario.")
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

                reset_buffer(reset_header=True)
                st.session_state["salvato"] = True
                st.rerun()

# ============================================================
# LOTTI IN CORSO
# ============================================================

if sezione_corrente == "Lotti in corso":
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

if sezione_corrente == "Qualità":
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
# PRODUCTION VS TARGET
# ============================================================

if sezione_corrente == "Production vs Target":
    st.subheader("📈 Production vs. Target Report")
    st.caption("Daily, Weekly, Monthly, Year-to-Date | Output fisico e output equivalente standard 40%")

    aggiorna_lotti_da_eventi()
    lotti_report = prepara_lotti_per_production_report(leggi_lotti())
    storico = leggi_storico_mensile()

    basis = st.radio(
        "Base di lettura",
        ["Physical Powder (kg)", "Standard Equivalent Output 40% (kg eq.)"],
        horizontal=True,
        help="Physical Powder usa i kg fisici di polvere finale. Standard Equivalent normalizza i prodotti alla base 40% di estratto puro."
    )
    col_valore = "kg_polvere_finale" if basis.startswith("Physical") else "kg_equivalenti_standard"
    col_target = "kg_fisici" if basis.startswith("Physical") else "kg_equivalenti_40"
    label_valore = "Physical Powder (kg)" if basis.startswith("Physical") else "Standard Equivalent 40% (kg eq.)"

    oggi = datetime.today().date()
    ieri = oggi - pd.Timedelta(days=1)
    inizio_settimana = oggi - pd.Timedelta(days=oggi.weekday())
    inizio_mese = oggi.replace(day=1)
    inizio_anno = oggi.replace(month=1, day=1)

    # Target provvisorio: media storica mensile caricata dall'utente. In assenza di storico resta n.d.
    target_mese = media_storica_mensile(col_target)
    target_giorno = safe_div(target_mese, 22) if target_mese > 0 else 0
    target_settimana = target_giorno * 5 if target_giorno > 0 else 0
    target_ytd = target_mese * oggi.month if target_mese > 0 else 0

    periods = [
        ("Yesterday", ieri, ieri, target_giorno),
        ("Week-to-Date", inizio_settimana, oggi, target_settimana),
        ("Month-to-Date", inizio_mese, oggi, target_mese),
        ("Year-to-Date", inizio_anno, oggi, target_ytd),
    ]

    rows = []
    for nome, start, end, target in periods:
        s_periodo = somma_periodo(lotti_report, start, end)
        actual = s_periodo["kg_fisici"] if basis.startswith("Physical") else s_periodo["kg_equivalenti_40"]
        rows.append({
            "Period": nome,
            "Actual": actual,
            "Historical Average / Target": target,
            "Variance vs Target": format_delta(actual, target),
            "Closed lots": s_periodo["lotti"],
        })

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Yesterday", f"{rows[0]['Actual']:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))
    k2.metric("Week-to-Date", f"{rows[1]['Actual']:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))
    k3.metric("Month-to-Date", f"{rows[2]['Actual']:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))
    k4.metric("Year-to-Date", f"{rows[3]['Actual']:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.markdown(f"### Production by period – {label_valore}")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if storico.empty:
        st.info("Storico mensile non ancora caricato. La pagina è predisposta: quando importerai lo storico, la dashboard calcolerà la media mensile e la userà come baseline/target iniziale.")
    else:
        st.success("Storico mensile disponibile: la baseline è calcolata come media dei mesi storici caricati.")
        st.dataframe(storico, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Trend produzione")
    if lotti_report.empty:
        st.info("Nessun lotto chiuso disponibile per costruire il trend.")
    else:
        trend = lotti_report.copy()
        trend["mese"] = trend["data_report"].dt.to_period("M").astype(str)
        trend_g = trend.groupby("mese", as_index=False).agg(
            physical_kg=("kg_polvere_finale", "sum"),
            equivalent_kg_40=("kg_equivalenti_standard", "sum"),
            lots=("lotto_molle", "count"),
        )
        y_col = "physical_kg" if basis.startswith("Physical") else "equivalent_kg_40"
        fig = px.bar(trend_g, x="mese", y=y_col, text_auto=".1f", title=f"Monthly production trend – {label_valore}")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("### Caricamento storico mensile")
    st.caption("Formato atteso: mese, kg_fisici, kg_equivalenti_40, giorni_produttivi, note. Esempio mese: 2025-01.")

    uploaded_storico = st.file_uploader("Carica storico mensile CSV", type=["csv"], key="upload_storico_mensile")
    if uploaded_storico is not None:
        try:
            df_up = pd.read_csv(uploaded_storico, dtype=str).fillna("")
            for col in COL_STORICO_MENSILE:
                if col not in df_up.columns:
                    df_up[col] = ""
            salva_storico_mensile(df_up[COL_STORICO_MENSILE])
            st.success("Storico mensile importato correttamente. Ricarica la pagina o cambia sezione per aggiornare la baseline.")
        except Exception as e:
            st.error(f"Errore import storico mensile: {e}")

    template = pd.DataFrame(columns=COL_STORICO_MENSILE).to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Scarica template storico mensile CSV",
        data=template,
        file_name="template_storico_mensile_spray_dryer.csv",
        mime="text/csv",
        type="secondary",
        key="download_template_storico_mensile",
    )


# ============================================================
# CRUSCOTTO
# ============================================================

if sezione_corrente == "Cruscotto OEE":
    st.subheader("📊 Cruscotto OEE")

    aggiorna_lotti_da_eventi()
    eventi = prepara_eventi(leggi_eventi())
    lotti = prepara_lotti(leggi_lotti())

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

    if eventi.empty:
        st.info("Nessun dato disponibile. Il cruscotto è pronto e si aggiornerà al primo turno salvato.")

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
        key="download_button_1",
        )

# ============================================================
# ASSUNZIONI E FORMULE
# ============================================================

if sezione_corrente == "Assunzioni e formule":
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

if sezione_corrente == "Anagrafica prodotti":
    st.subheader("📚 Anagrafica prodotti")

    prodotti = leggi_prodotti()

    if len(prodotti) == 1 and str(prodotti.iloc[0]["codice_prodotto"]) == "INSERIRE":
        st.warning("Anagrafica prodotti non caricata. Carica il file data/prodotti.csv incluso nel pacchetto.")

    st.dataframe(visualizza_prodotti(prodotti), use_container_width=True)

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
    key="download_button_2",
    )


# ============================================================
# CONFIGURAZIONE
# ============================================================

if sezione_corrente == "Configurazione":
    st.subheader("⚙️ Configurazione causali e calendario fermi")

    st.markdown("## Causali evento")
    causali = leggi_causali()
    st.dataframe(visualizza_causali(causali), use_container_width=True)

    with st.form("form_causale"):
        nuova_causale = st.text_input("Nome causale")
        categoria = st.selectbox("Categoria", ["Fermo programmato", "Fermo non programmato"])
        c1, c2, c3 = st.columns(3)
        with c1:
            escludi = st.selectbox("Escludi dal tempo pianificato OEE", ["NO", "SI"])
        with c2:
            perdita = st.selectbox("Perdita di disponibilità", ["SI", "NO"])
        with c3:
            attiva = st.selectbox("Attiva", ["SI", "NO"])
        salva_c = st.form_submit_button("Salva causale", type="primary")

    if salva_c:
        if nuova_causale.strip() == "":
            st.error("Inserisci il nome della causale.")
        else:
            nuovo = pd.DataFrame([{
                "causale": nuova_causale.strip(),
                "categoria": categoria,
                "escludi_da_tempo_pianificato": escludi,
                "perdita_disponibilita": perdita,
                "attiva": attiva,
            }])
            causali = pd.concat([causali, nuovo], ignore_index=True)
            causali = causali.drop_duplicates(subset=["causale"], keep="last")
            salva_csv(causali, CAUSALI_FILE, COL_CAUSALI)
            st.session_state["salvato"] = True
            st.rerun()

    st.divider()
    st.markdown("## Calendario fermi programmati")

    fp = prepara_fermi_programmati(leggi_fermi_programmati())
    st.dataframe(visualizza_fermi_programmati(fp), use_container_width=True)

    with st.form("form_fermo_programmato"):
        d = st.date_input("Data fermo", value=None, format="DD/MM/YYYY")
        orari = lista_orari_15min()
        a, b = st.columns(2)
        with a:
            oi = st.selectbox("Ora inizio", ["-- Seleziona --"] + orari)
        with b:
            of = st.selectbox("Ora fine", ["-- Seleziona --"] + orari)
        causali_prog = leggi_causali()
        causali_prog = causali_prog[causali_prog["escludi_da_tempo_pianificato"].astype(str).str.upper()=="SI"]["causale"].astype(str).tolist()
        causale = st.selectbox("Causale", ["-- Seleziona causale --"] + causali_prog)
        note = st.text_area("Note")
        salva_fp = st.form_submit_button("Salva fermo programmato", type="primary")

    if salva_fp:
        if d is None or oi.startswith("--") or of.startswith("--") or causale.startswith("--"):
            st.error("Compila data, ora inizio, ora fine e causale.")
        else:
            durata = ore_da_orari(parse_time_manual(oi), parse_time_manual(of))
            if durata <= 0:
                st.error("Durata non valida.")
            else:
                nuovo = pd.DataFrame([{
                    "id_fermo_programmato": nuovo_id(),
                    "data": str(d),
                    "ora_inizio": oi,
                    "ora_fine": of,
                    "durata_h": durata,
                    "causale": causale,
                    "note": note,
                }])
                fpx = leggi_fermi_programmati()
                fpx = pd.concat([fpx, nuovo], ignore_index=True)
                salva_csv(fpx, FERMI_PROGRAMMATI_FILE, COL_FERMI_PROGRAMMATI)
                st.session_state["salvato"] = True
                st.rerun()

    if not fp.empty:
        id_del = st.selectbox("Fermo programmato da eliminare", fp["id_fermo_programmato"].astype(str).tolist())
        if st.button("Elimina fermo programmato", type="secondary"):
            fpx = leggi_fermi_programmati()
            fpx = fpx[fpx["id_fermo_programmato"].astype(str) != str(id_del)]
            salva_csv(fpx, FERMI_PROGRAMMATI_FILE, COL_FERMI_PROGRAMMATI)
            st.session_state["salvato"] = True
            st.rerun()


# ============================================================
# GESTIONE DATI
# ============================================================

if sezione_corrente == "Gestione dati":
    st.subheader("🔒 Gestione dati")

    eventi = leggi_eventi()
    lotti = leggi_lotti()

    st.markdown("## Ultimi eventi registrati")

    if eventi.empty:
        st.info("Nessun evento registrato.")
    else:
        ultimi_eventi = eventi.tail(20).iloc[::-1]
        st.dataframe(visualizza_eventi(ultimi_eventi), use_container_width=True)

    st.divider()
    st.markdown("## Area modifica protetta")

    password = st.text_input("Password gestione", type="password")

    if password != ADMIN_PASSWORD:
        st.info("Inserisci la password per modificare o cancellare dati già salvati.")
        st.stop()

    st.success("Accesso gestione abilitato.")

    st.markdown("## Eventi turno")
    st.dataframe(visualizza_eventi(eventi), use_container_width=True)

    if not eventi.empty:
        st.markdown("### Modifica evento salvato")

        id_evento_mod = st.selectbox(
            "Evento da modificare",
            eventi["id_evento"].astype(str).tolist(),
            key="evento_da_modificare_gestione"
        )

        evento_sel = eventi[eventi["id_evento"].astype(str) == str(id_evento_mod)].iloc[0]

        with st.form("form_modifica_evento_salvato"):
            c1, c2, c3 = st.columns(3)
            with c1:
                nuova_data = st.text_input("Data", value=str(evento_sel.get("data", "")))
            with c2:
                nuovo_turno = st.selectbox(
                    "Turno",
                    ["1", "2", "3"],
                    index=["1", "2", "3"].index(str(evento_sel.get("turno", "1"))) if str(evento_sel.get("turno", "1")) in ["1", "2", "3"] else 0
                )
            with c3:
                nuovo_tipo_evento = st.selectbox(
                    "Tipo evento",
                    ["Produzione"] + causali_attive(),
                    index=(["Produzione"] + causali_attive()).index(str(evento_sel.get("tipo_evento", "Produzione"))) if str(evento_sel.get("tipo_evento", "Produzione")) in (["Produzione"] + causali_attive()) else 0
                )

            c4, c5, c6 = st.columns(3)
            with c4:
                nuova_ora_inizio = st.text_input("Ora inizio", value=str(evento_sel.get("ora_inizio", ""))[:5])
            with c5:
                nuova_ora_fine = st.text_input("Ora fine", value=str(evento_sel.get("ora_fine", ""))[:5])
            with c6:
                nuovo_lotto = st.text_input("Lotto molle", value=str(evento_sel.get("lotto_molle", "")))

            nuova_nota = st.text_area("Note", value=str(evento_sel.get("note", "")))

            salva_modifica_evento = st.form_submit_button("Salva modifica evento", type="primary")

        if salva_modifica_evento:
            ora_i = parse_time_manual(nuova_ora_inizio)
            ora_f = parse_time_manual(nuova_ora_fine)
            nuova_durata = ore_da_orari(ora_i, ora_f) if ora_i and ora_f else 0

            if nuova_durata <= 0:
                st.error("Orari non validi. Usa il formato HH:MM.")
            else:
                mask = eventi["id_evento"].astype(str) == str(id_evento_mod)

                aggiornamenti = {
                    "data": nuova_data,
                    "turno": nuovo_turno,
                    "tipo_evento": nuovo_tipo_evento,
                    "ora_inizio": str(ora_i),
                    "ora_fine": str(ora_f),
                    "durata_h": nuova_durata,
                    "lotto_molle": nuovo_lotto,
                    "note": nuova_nota,
                }

                for col, val in aggiornamenti.items():
                    eventi[col] = eventi[col].astype("object")
                    eventi.loc[mask, col] = str(val)

                salva_csv(eventi, EVENTI_FILE, COL_EVENTI)
                aggiorna_lotti_da_eventi()
                st.session_state["salvato"] = True
                st.rerun()

        st.markdown("### Elimina evento")

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
    key="download_button_3",
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
    key="download_button_4",
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
                if "causali" in imported:
                    salva_csv(imported["causali"], CAUSALI_FILE, COL_CAUSALI)
                if "fermi_programmati" in imported:
                    salva_csv(imported["fermi_programmati"], FERMI_PROGRAMMATI_FILE, COL_FERMI_PROGRAMMATI)
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
