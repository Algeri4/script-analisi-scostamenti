# fixed_costs_budget.py  (legge costi2021.csv senza header)
import pandas as pd
from config import *

print("=== FIXED COSTS BUDGET 2022 (base costi2021.csv) ============")

# ---------- 1. lettura ----------
costi21 = pd.read_csv("../input/costi2021.csv",
                      sep=";", decimal=",", header=None,
                      names=["Voce", "Valore"])
costi21["Valore"] = pd.to_numeric(costi21["Valore"], errors="coerce")
print("Voci lette 2021:")
print(costi21)

# ---------- 2. dizionario rapido ----------
v21 = dict(zip(costi21["Voce"], costi21["Valore"]))

# ---------- 3. costi fissi di produzione ----------
print("\n=== COSTI FISSI DI PRODUZIONE ===")
voce_prod = [
    "COSTO DEL PERSONALE",
    "MANUTENZIONI",
    "ALTRI ONERI DEL PERSONALE",
    "ASSICURAZIONI",
    "CONSULENZE TECNICHE E CANONI ACQUE",
    "COSTO PER GODIMENTO DI BENI DI TERZI"
]
for v in voce_prod:
    if v not in v21:
        raise KeyError(f"Voce mancante: {v}")

val_prod = [
    v21["COSTO DEL PERSONALE"] - AUMENTO_CCNL_TOTALE_ANNUO,
    v21["MANUTENZIONI"] + RIBASSO_MANUTENZIONI_BUDGET,
    v21["ALTRI ONERI DEL PERSONALE"] * (1 + AUMENTO_GENERICO_2_5_PERC),
    v21["ASSICURAZIONI"] * (1 + AUMENTO_GENERICO_2_5_PERC),
    v21["CONSULENZE TECNICHE E CANONI ACQUE"] * (1 + AUMENTO_GENERICO_2_5_PERC),
    v21["COSTO PER GODIMENTO DI BENI DI TERZI"] * (1 + AUMENTO_GENERICO_2_5_PERC)
]
tot_prod = sum(val_prod)

# stampa ogni voce
for v, imp in zip(voce_prod, val_prod):
    print(f"{v:<50} {imp:>15,.2f} euro")
print(f"{'Totale budget costi fissi di produzione':<50} {tot_prod:>15,.2f} euro")

# ---------- 4. costi di struttura ----------
print("\n=== COSTI DI STRUTTURA ===")
voce_strutt = [
    "CONSULENZE E AMMINISTRATORI ",
    "SPESE UFFICIO VARIE E ONERI DIVERSI DI GESTIONE",
    "IMPOSTE E TASSE VARIE NON SUL REDDITO"
]
for v in voce_strutt:
    if v not in v21:
        raise KeyError(f"Voce mancante: {v}")

val_strutt = [
    v21["CONSULENZE E AMMINISTRATORI "] * (1 + AUMENTO_GENERICO_2_5_PERC),
    v21["SPESE UFFICIO VARIE E ONERI DIVERSI DI GESTIONE"] * (1 + AUMENTO_GENERICO_2_5_PERC),
    v21["IMPOSTE E TASSE VARIE NON SUL REDDITO"] * (1 + AUMENTO_GENERICO_2_5_PERC)
]
tot_strutt = sum(val_strutt)

for v, imp in zip(voce_strutt, val_strutt):
    print(f"{v:<50} {imp:>15,.2f} euro")
print(f"{'Totale budget costi struttura comm./amm.va':<50} {tot_strutt:>15,.2f} euro")

# ---------- 5. TOTALE GENERALE ----------
totale_generale = tot_prod + tot_strutt
print(f"\n{'TOTALE BUDGET COSTI FISSI':<50} {totale_generale:>15,.2f} euro")

# ---------- 6. tabella finale ESATTA (nessuna voce in più) ----------
riep = pd.DataFrame({
    "Voce": [
        "Costo del personale",
        "Manutenzioni",
        "Altri oneri del personale",
        "Assicurazioni",
        "Consulenze tecniche e canoni acque",
        "Costo per godimento di beni di terzi",
        "Totale budget costi fissi di produzione",
        "Consulenze e amministrazioni",
        "Spese ufficio varie e oneri diversi di gestione",
        "Imposte e tasse varie non sul reddito",
        "Totale budget costi struttura comm./amm.va",
        "TOTALE BUDGET COSTI FISSI"
    ],
    "Valore Budget (euro)": [
        val_prod[0], val_prod[1], val_prod[2], val_prod[3], val_prod[4], val_prod[5], tot_prod,
        val_strutt[0], val_strutt[1], val_strutt[2], tot_strutt,
        totale_generale
    ]
})

print("\nTabella finale:")
print(riep)

# ---------- 7. salva ----------
riep.to_csv("../output/FixedCostsBudget.csv", index=False, sep=";", decimal=",")
print("\nFile FixedCostsBudget.csv creato.")