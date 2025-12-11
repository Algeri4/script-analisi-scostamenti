# data_loader.py
import pandas as pd
import os
from config import BASE_PATH   # se hai messo BASE_PATH in config, altrimenti definiscilo qui

FILES = {
    "conto_economico_consuntivo": "contoEconomicoConsuntivo2022.CSV",
    "budget_vendite": "budgetVendite2022.CSV",
    "consuntivo": "consuntivo2022.CSV",
    "costi_2021": "costi2021.CSV"
}

def load_all() -> dict:
    """Carica tutti i CSV e restituisce un dizionario di DataFrame."""
    dfs = {}
    for name, filename in FILES.items():
        path = os.path.join(BASE_PATH, filename)
        if os.path.isfile(path):
            dfs[name] = pd.read_csv(path,
                                    encoding='latin1',
                                    sep=';',
                                    decimal=',')
            print(f"✅ {name}: {dfs[name].shape[0]} righe, {dfs[name].shape[1]} colonne")
        else:
            print(f"❌ File mancante: {path}")
    return dfs