import pandas as pd
from config import *

print("=== ANALISI SCOSTAMENTI BASE 2022 ===")

# -----------------------------
# 1) Leggo CE Budget (output)
# -----------------------------
ce_budget = pd.read_csv("../output/CE_Budget_2022.csv", sep=";", decimal=",", thousands=".")
ce_budget.columns = ["Voce", "Budget"]

# -----------------------------
# 2) Leggo CE Consuntivo (input) - attenzione: spesso è senza header
# -----------------------------
ce_cons = pd.read_csv(
    "../input/contoEconomicoConsuntivo2022.csv",
    sep=";",
    decimal=",",
    thousands=".",
    header=None,
    names=["Voce", "Reale"]
)

# pulizia
ce_budget["Voce"] = ce_budget["Voce"].astype(str).str.strip()
ce_cons["Voce"] = ce_cons["Voce"].astype(str).str.strip()
ce_budget["Budget"] = pd.to_numeric(ce_budget["Budget"], errors="coerce").fillna(0.0)
ce_cons["Reale"] = pd.to_numeric(ce_cons["Reale"], errors="coerce").fillna(0.0)

# -----------------------------
# 3) Merge + delta
# -----------------------------
df = pd.merge(ce_budget, ce_cons, on="Voce", how="left").fillna(0.0)
df["Δ Reale-Budget"] = df["Reale"] - df["Budget"]

# -----------------------------
# 4) Stampa controllo
# -----------------------------
print("\nPrime righe:")
print(df.head(10))

print("\nUltime righe:")
print(df.tail(10))

# -----------------------------
# 5) Salvo
# -----------------------------
#df.to_csv("../output/AnalisiDegliScostamenti.csv", index=False, sep=";", decimal=",")

#print("\nFile AnalisiDegliScostamenti.csv creato.")
