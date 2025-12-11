# variable_costs_budget.py  (legge correttamente migliaia e decimali)
import pandas as pd
from config import *

print("=== 0. lettura budgetRicavi.csv ============")
# leggo subito con il separatore decimale e migliaia corretti
budget = pd.read_csv("../output/budgetRicavi.csv",
                     sep=";", decimal=",", thousands=".")

print("prime 5 rigo lette:")
print(budget[["Articolo","Categoria","Famiglia","Quantita (kg)","Prezzo e/kg","CMP e/kg (con dazio)"]].head())

print("\n=== 1. quantita per famiglia (ton) ============")
fam_ton = budget.groupby("Famiglia")["Quantita (kg)"].sum() / 1000
print(fam_ton)
ton_A = fam_ton.get("A", 0.0) + fam_ton.get("PCL", 0.0)
ton_V = fam_ton.get("V", 0.0)
ton_P = fam_ton.get("P", 0.0)
ton_tot = ton_A + ton_V + ton_P
print(f"A: {ton_A:,.2f} t")
print(f"V: {ton_V:,.2f} t")
print(f"P: {ton_P:,.2f} t")
print(f"totale: {ton_tot:,.2f} t")

print("\n=== 2. vapore (ton) ============")
vap_A = ton_A * CONS_TON_VAP_PER_TON_PF_A
vap_V = ton_V * CONS_TON_VAP_PER_TON_PF_V
vap_P = ton_P * FATTORE_EMULSIONI_VINILICHE_PER_P * CONS_TON_VAP_PER_TON_PF_V
vap_tot = vap_A + vap_V + vap_P
print(f"vapore A: {vap_A:,.2f} t")
print(f"vapore V: {vap_V:,.2f} t")
print(f"vapore P: {vap_P:,.2f} t")
print(f"vapore totale: {vap_tot:,.2f} t")

print("\n=== 3. metano ============")
smc_tot = vap_tot * SMC_METANO_PER_TON_VAPORE
print(f"smc totali: {smc_tot:,.0f}")
prezzo_smc_2022 = 0.4733720930232559 * (1 + AUMENTO_COSTO_METANO_2022)
print(f"prezzo smc 2022: {prezzo_smc_2022:.4f} euro/smc")
costo_metano = smc_tot * prezzo_smc_2022
print(f"costo metano: {costo_metano:,.2f} euro")

print("\n=== 4. energia elettrica ============")
kwh_A = ton_A * KWH_PER_TON_PF_A
kwh_V = ton_V * KWH_PER_TON_PF_V
kwh_P = ton_P * (KWH_PER_TON_PF_P + KWH_PER_TON_PF_V * FATTORE_EMULSIONI_VINILICHE_PER_P)
kwh_serv = KWH_SERVIZI_GENERALI_MENSILI * 12
kwh_tot = kwh_A + kwh_V + kwh_P + kwh_serv
print(f"kWh A: {kwh_A:,.0f}")
print(f"kWh V: {kwh_V:,.0f}")
print(f"kWh P: {kwh_P:,.0f}")
print(f"kWh servizi: {kwh_serv:,.0f}")
print(f"kWh totali: {kwh_tot:,.0f}")
prezzo_kwh_2022 = 0.15721518991224825 * (1 + AUMENTO_COSTO_ENERGIA_ELETTRICA_2022)
print(f"prezzo kWh 2022: {prezzo_kwh_2022:.4f} euro/kWh")
costo_eel = kwh_tot * prezzo_kwh_2022
print(f"costo energia elettrica: {costo_eel:,.2f} euro")

print("\n=== 5. CO₂ ============")
ton_co2 = vap_tot * QUOTA_CO2_DA_ACQUISTARE
print(f"t CO₂ da acquistare: {ton_co2:,.2f}")
costo_co2 = ton_co2 * COSTO_QUOTA_CO2_PER_TON_VAPORE
print(f"costo quota CO₂: {costo_co2:,.2f} euro")

print("\n=== 6. materiali di consumo ============")
costo_mat_cons = 150_000 * (1 + INFLAZIONE_2022_SU_2021)
print(f"costo materiali consumo 2022: {costo_mat_cons:,.2f} euro")

print("\n=== 7. pulizia e smaltimento ============")
ton_emuls = ton_V + ton_A + ton_P * FATTORE_EMULSIONI_VINILICHE_PER_P
print(f"t emulsioni (V+P): {ton_emuls:,.2f} t")
costo_smalt = ton_emuls * COSTO_SMALTIMENTO_PER_TON_EMULSIONI
print(f"costo smaltimento: {costo_smalt:,.2f} euro")

print("\n=== 8. trasporti ============")
print(f"costo trasporto per t 2022: {COSTO_TRASPORTO_2022_PER_TON:.2f} euro/t")
costo_trasp = ton_tot * COSTO_TRASPORTO_2022_PER_TON
print(f"costo trasporti vendita: {costo_trasp:,.2f} euro")

print("\n=== 9. provvigioni ============")
ricavi_polveri = budget[budget["Famiglia"] == "P"]["Ricavo"].sum()
print(f"ricavi polveri: {ricavi_polveri:,.2f} euro")
provv = ricavi_polveri * PROVVIGIONI_PERC_SU_POLVERI
print(f"provvigioni 2%: {provv:,.2f} euro")

print("\n=== 10. tabella riepilogativa ============")
riep = pd.DataFrame({
    "Voce": ["Metano", "Energia elettrica", "Materiali di consumo",
             "Pulizia e smaltimento rifiuti", "Trasporti vendita",
             "Provvigioni su vendite", "Quota CO₂"],
    "Valore Budget (euro)": [costo_metano, costo_eel, costo_mat_cons,
                             costo_smalt, costo_trasp, provv, costo_co2]
})
print(riep)

print(riep["Valore Budget (euro)"].sum())
# ---------- 11. salva ----------
riep.to_csv("../output/VariableCostsBudget.csv", index=False, sep=";", decimal=",")
print("\nFile VariableCostsBudget.csv creato.")