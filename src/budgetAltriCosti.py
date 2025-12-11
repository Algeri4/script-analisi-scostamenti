# others_budget.py  (solo parametri config.py)
import pandas as pd
from config import *
from datetime import date
costi21 = pd.read_csv("../input/costi2021.csv",
                      sep=";", decimal=",", header=None,
                      names=["Voce", "Valore"])
costi21["Valore"] = pd.to_numeric(costi21["Valore"], errors="coerce")

# ---------- 2. dizionario rapido ----------
v21 = dict(zip(costi21["Voce"], costi21["Valore"]))


print("=== ALTRI COSTI BUDGET 2022 ============")

# ---------- 1. singole voci ----------
amm_imm = -v21['AMMORTAMENTI IMMOBILIZZAZIONI IMMATERIALI']
amm_mat = -v21['AMMORTAMENTI IMMOBILIZZAZIONI MATERIALI'] + INVESTIMENTO_NUOVO_IMPIANTO * QUOTA_PRIMO_ANNO
sval_cred = 0 if not PREVISTE_SVALUTAZIONI_CREDITI else 0   # 0 = non previste
inizio = date.fromisoformat(DATA_AVVIO_LINEA)   # 2022-06-01
fine_anno = date(inizio.year, 12, 31)           # 2022-12-31
giorni_attivi = (fine_anno - inizio).days + 1   # +1 per includere il 1-giu
oneri_fin = NUOVA_LINEA_DI_CREDITO * TASSO_INTERESSE_NUOVA_LINEA * giorni_attivi / 365                        # dato budget
prov_fin = 0 if not PREVISTI_PROVENTI_FINANZIARI else 0
oneri_stra = 0 if not PREVISTI_ONERI_STRAORDINARI else 0
prov_stra = 0 if not PREVISTI_PROVENTI_STRAORDINARI else 0
sval_acc = 0 if not PREVISTE_SVALUTAZIONI_ACCANTONAMENTI else 0
imposte = 0    # dato budget

# ---------- 2. stampa dettaglio ----------
print(f"{'Ammortamenti immobilizzazioni immateriali':<50} {amm_imm:>15,.2f} euro")
print(f"{'Ammortamenti immobilizzazioni materiali':<50} {amm_mat:>15,.2f} euro")
print(f"{'Svalutazione crediti':<50} {sval_cred:>15,.2f} euro")
print(f"{'Oneri finanziari':<50} {oneri_fin:>15,.2f} euro")
print(f"{'Proventi finanziari':<50} {prov_fin:>15,.2f} euro")
print(f"{'Oneri straordinari':<50} {oneri_stra:>15,.2f} euro")
print(f"{'Proventi straordinari':<50} {prov_stra:>15,.2f} euro")
print(f"{'Svalutazioni-accantonamenti':<50} {sval_acc:>15,.2f} euro")
print(f"{'Imposte sul reddito':<50} {imposte:>15,.2f} euro")

# ---------- 3. TOTALE ----------
totale = amm_imm + amm_mat + sval_cred + oneri_fin + prov_fin + oneri_stra + prov_stra + sval_acc + imposte
print(f"{'TOTALE ALTRI COSTI':<50} {totale:>15,.2f} euro")

# ---------- 4. tabella finale ESATTA ----------
riep = pd.DataFrame({
    "Voce": [
        "Ammortamenti immobilizzazioni immateriali",
        "Ammortamenti immobilizzazioni materiali",
        "Svalutazione crediti",
        "Oneri finanziari",
        "Proventi finanziari",
        "Oneri straordinari",
        "Proventi straordinari",
        "Svalutazioni-accantonamenti",
        "Imposte sul reddito",
        "TOTALE ALTRI COSTI"
    ],
    "Valore Budget (euro)": [
        amm_imm, amm_mat, sval_cred, oneri_fin, prov_fin,
        oneri_stra, prov_stra, sval_acc, imposte, totale
    ]
})

print("\nTabella finale:")
print(riep)

# ---------- 5. salva ----------
riep.to_csv("../output/OthersBudget.csv", index=False, sep=";", decimal=",")
print("\nFile OthersBudget.csv creato.")