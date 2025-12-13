import re
from pathlib import Path
from datetime import datetime
import pandas as pd

from config import *  # usa le vostre costanti

print("=== ANALISI SCOSTAMENTI BASE 2022 ===")

# -------------------------------------------------------
# Loader: leggo tutti i CSV in input e output
# -------------------------------------------------------
def load_all_csv(folder, sep=";", decimal=",", thousands="."):
    folder = Path(folder)
    out = {}
    for p in folder.glob("*.csv"):
        try:
            df = pd.read_csv(p, sep=sep, decimal=decimal, thousands=thousands)
        except Exception:
            df = pd.read_csv(p, sep=sep, decimal=decimal, thousands=thousands, engine="python")
        out[p.name] = df
    return out

DATA = {
    "input": load_all_csv("../input"),
    "output": load_all_csv("../output"),
}

def safe_to_csv(df, path_str, sep=";", decimal=","):
    path = Path(path_str)
    try:
        df.to_csv(path, index=False, sep=sep, decimal=decimal)
        print(f"\nFile creato: {path.as_posix()}")
    except PermissionError:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        alt = path.with_name(f"{path.stem}__LOCKED_{ts}{path.suffix}")
        df.to_csv(alt, index=False, sep=sep, decimal=decimal)
        print(f"\nATTENZIONE: {path.name} è bloccato (Excel aperto).")
        print(f"Ho salvato invece: {alt.as_posix()}")

# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def norm_voce(s: str) -> str:
    s = str(s).replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip().upper()

def to_num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0.0)

def _get(out_df, col, voce):
    m = out_df["Voce"].astype(str).str.strip().map(norm_voce).eq(norm_voce(voce))
    return float(out_df.loc[m, col].sum())

def _set(out_df, col, voce, value):
    m = out_df["Voce"].astype(str).str.strip().map(norm_voce).eq(norm_voce(voce))
    out_df.loc[m, col] = float(value)

# -------------------------------------------------------
# 1) Budget: da output/CE_Budget_2022.csv
# -------------------------------------------------------
ce_budget = DATA["output"]["CE_Budget_2022.csv"].copy()
ce_budget.columns = ["Voce", "Budget"]
ce_budget["Voce"] = ce_budget["Voce"].astype(str).str.strip()
ce_budget["Budget"] = to_num(ce_budget["Budget"])

# -------------------------------------------------------
# 2) Reale: da input/contoEconomicoConsuntivo2022.csv
#    (lettura sempre header=None per evitare “PF = 0”)
# -------------------------------------------------------
ce_reale = pd.read_csv(
    "../input/contoEconomicoConsuntivo2022.csv",
    sep=";",
    decimal=",",
    thousands=".",
    header=None,
    names=["Voce", "Reale"]
)
ce_reale["Voce"] = ce_reale["Voce"].astype(str).str.strip()
ce_reale["Reale"] = to_num(ce_reale["Reale"])

# -------------------------------------------------------
# 3) Merge su voce normalizzata (robusto agli spazi)
# -------------------------------------------------------
b = ce_budget.copy()
r = ce_reale.copy()
b["_k"] = b["Voce"].map(norm_voce)
r["_k"] = r["Voce"].map(norm_voce)

out = b.merge(r[["_k", "Reale"]], on="_k", how="left").fillna({"Reale": 0.0})
out.drop(columns=["_k"], inplace=True)

# -------------------------------------------------------
# 4) FIX SEGNI BUDGET: i costi devono essere negativi
# -------------------------------------------------------
VOCI_COSTO_BUDGET_NEG = [
    "ACQUISTO MATERIE PRIME",
    "B)  TOTALE COSTI MATERIE PRIME",
    "COSTO ENERGIA TOTALE",
    "MATERIALI DI CONSUMO",
    "PULIZIA E SMALTIMENTO RIFIUTI",
    "C)  COSTI VARIABILI DI PRODUZIONE",
    "TRASPORTI E ONERI DI VENDITA + ACQUISTO",
    "COSTO DI VENDITA - PROVVIGIONI-ENASARCO",
    "D)  TOTALE COSTI DI VENDITA",

    "COSTO DEL PERSONALE",
    "MANUTENZIONI",
    "ALTRI ONERI DEL PERSONALE",
    "ASSICURAZIONI",
    "CONSULENZE TECNICHE E CANONI ACQUE",
    "COSTO PER GODIMENTO DI BENI DI TERZI",
    "F) TOTALE COSTI FISSI DI PRODUZIONE",

    "CONSULENZE E AMMINISTRATORI",
    "SPESE UFFICIO VARIE E ONERI DIVERSI DI GESTIONE",
    "IMPOSTE E TASSE VARIE NON SUL REDDITO",
    "G) TOTALE COSTI STRUTTURA COMM./AMM.VA",

    "AMMORTAMENTI IMMOBILIZZAZIONI IMMATERIALI",
    "AMMORTAMENTI IMMOBILIZZAZIONI MATERIALI",
    "SVALUTAZIONE CREDITI",
    "I) TOTALE AMMORTAMENTI",

    "(ONERI FINANZIARI)",
    "M)  ONERI E PROVENTI FINANZIARI NETTI",
    "IMPOSTE SUL REDDITO",
]

mask_costi = out["Voce"].map(norm_voce).isin({norm_voce(v) for v in VOCI_COSTO_BUDGET_NEG})
out.loc[mask_costi, "Budget"] = -out.loc[mask_costi, "Budget"].abs()

# -------------------------------------------------------
# 5) ALTRI RICAVI reale: calcolato da config.py (non hardcoded)
#    NB: queste costanti devono esistere in config.py
# -------------------------------------------------------
required = [
    "QTA_SPESE_TRASPORTO_CONS_2022",
    "COSTO_PER_UNITA_TRASPORTO_CONS_2022",
    "QTA_PREMIO_YEAR21_CONS_2022",
    "COSTO_PER_UNITA_PREMIO_CONS_2022",
    "QTA_ADEBITI_VARI_CONS_2022",
    "COSTO_PER_UNITA_ADEBITI_VARI_CONS_2022",
]
missing = [k for k in required if k not in globals()]
if missing:
    raise KeyError(f"Mancano in config.py queste costanti per calcolare 'ALTRI RICAVI' reale: {missing}")

altri_ricavi_reale = (
    QTA_SPESE_TRASPORTO_CONS_2022 * COSTO_PER_UNITA_TRASPORTO_CONS_2022
    - QTA_PREMIO_YEAR21_CONS_2022 * COSTO_PER_UNITA_PREMIO_CONS_2022
    + QTA_ADEBITI_VARI_CONS_2022 * COSTO_PER_UNITA_ADEBITI_VARI_CONS_2022
)

_set(out, "Reale", "ALTRI RICAVI E LAVORI IN ECONOMIA", altri_ricavi_reale)

# -------------------------------------------------------
# 6) Ricalcolo A) TOTALE RICAVI PRODUZIONE (Reale) coerente con le voci sopra
# -------------------------------------------------------
A_reale = (
    _get(out, "Reale", "RICAVI DELLE VENDITE DI PRODOTTI FINITI")
    + _get(out, "Reale", "RICAVI DELLE VENDITE DI MATERIE PRIME - RIADDEBITI MP A GAMMA")
    + _get(out, "Reale", "RICAVI CONTO LAVORAZIONE - GAMMA E POLIKEMIA")
    + _get(out, "Reale", "ALTRI RICAVI E LAVORI IN ECONOMIA")
    + _get(out, "Reale", "VARIAZIONE PRODOTTI FINITI")
)
_set(out, "Reale", "A)  TOTALE RICAVI PRODUZIONE", A_reale)

# -------------------------------------------------------
# 7) Delta (colonna blu)
# -------------------------------------------------------
out["Δ Reale-Budget"] = out["Reale"] - out["Budget"]

# Round
for c in ["Budget", "Reale", "Δ Reale-Budget"]:
    out[c] = out[c].round(2)

out = out[["Voce", "Budget", "Reale", "Δ Reale-Budget"]]

# -------------------------------------------------------
# 8) Salvo
# -------------------------------------------------------
safe_to_csv(out, "../output/AnalisiDegliScostamentiBase.csv")
print("\nFatto.")

