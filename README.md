# OEE Spray Dryer – Versione 5.8.0

## Avvio

Aprire il terminale in questa cartella ed eseguire:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Su Windows, se il comando `python` non è disponibile, utilizzare `py`:

```bash
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

## Verifica della versione

Sotto il titolo dell'app deve comparire:

`Versione 5.8.0 – Qualità standard 95% | Production vs Target aggiornato`

## Dati

La cartella `data` viene creata automaticamente al primo avvio. Il vecchio export
Excel può essere importato successivamente dalla sezione Gestione dati.

## KPI principali

- Semilavorato totale
- Puro ottenuto
- Puro equivalente
- Taglio medio
- Qualità standard fissa al 95%

La sezione Production vs Target utilizza le stesse tre basi produttive.
