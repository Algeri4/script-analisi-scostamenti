# main.py
from data_loader import load_all
from config import *
import pandas as pd
import os

# ---------- 1. carico tutti i fogli ----------
dfs = load_all()

# ---------- 2. reference rapide ----------
df_ce   = dfs.get("conto_economico_consuntivo")
df_bv   = dfs.get("budget_vendite")
df_cons = dfs.get("consuntivo")
df_costi = dfs.get("costi_2021")


# ---------- 3. fix nomi colonne ---------- potete rinominarli se vi sono scomodi da scrivere ogni volta
df_bv.columns = ['Articolo', 'Categoria', 'Quantita (kg)',
                 'P medio (€/kg)', 'P medio ($/kg)',
                 'CMP medio (€/kg)', 'CMP medio ($/kg)', 'MP con dazio']

# ---------- 4. converto le colonne numeriche ----------
# lascio fare a pandas il parsing di migliaia e decimali
num_cols = ['Quantita (kg)',
            'P medio (€/kg)', 'P medio ($/kg)',
            'CMP medio (€/kg)', 'CMP medio ($/kg)']
for c in num_cols:
    df_bv[c] = pd.to_numeric(df_bv[c],
                             errors='coerce',
                             downcast='float')   # thousands='.', decimal=',' già fatti in read_csv

# ---------- 5. colonna PREZZO EURO ----------
ha_prezzo_eur = df_bv['P medio (€/kg)'].notna()
df_bv['Prezzo €/kg'] = df_bv['P medio (€/kg)'].where(
    ha_prezzo_eur,
    df_bv['P medio ($/kg)'] / EUR_TO_USD)

# ---------- 6. colonna CMP EURO ----------
ha_cmp_eur = df_bv['CMP medio (€/kg)'].notna()
df_bv['CMP €/kg'] = df_bv['CMP medio (€/kg)'].where(
    ha_cmp_eur,
    df_bv['CMP medio ($/kg)'] / EUR_TO_USD)

# ---------- 7. dazio ----------
mask_dazio   = df_bv['MP con dazio'].str.lower() == 'x'
mask_dollari = ~ha_cmp_eur
df_bv.loc[mask_dazio & mask_dollari, 'CMP €/kg'] *= (1 + DAZIO_PERC)

# ---------- 8. tabella finale ----------
out = df_bv[['Articolo', 'Categoria', 'Quantita (kg)']].copy()
out['Prezzo €/kg']        = df_bv['Prezzo €/kg']
out['CMP €/kg (con dazio)'] = df_bv['CMP €/kg']

# ---------- 9. salvo ----------
os.makedirs('../output', exist_ok=True)
out.to_csv('../output/budgetVendite_2022_clean.csv',
           index=False, sep=';', decimal='.')
print('Tabella riepilogativa creata:')
print(out.head())